from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from .models import Belief, BeliefType, EvidenceRef, EvidenceType, Scope, VersionValidity


@dataclass
class LLMConfig:
    base_url: str
    api_key: str
    model: str
    timeout_s: int = 60

    @classmethod
    def from_env(cls) -> "LLMConfig":
        api_key = os.getenv("BELIEFSYNC_LLM_API_KEY") or os.getenv("KIMI_API_KEY")
        base_url = os.getenv("BELIEFSYNC_LLM_BASE_URL") or os.getenv("KIMI_BASE_URL") or "https://api.moonshot.cn/v1"
        model = os.getenv("BELIEFSYNC_LLM_MODEL") or os.getenv("KIMI_MODEL") or "moonshot-v1-8k"
        timeout_s = int(os.getenv("BELIEFSYNC_LLM_TIMEOUT", "60"))
        if not api_key:
            raise ValueError(
                "No LLM API key found. Set BELIEFSYNC_LLM_API_KEY or KIMI_API_KEY in your environment."
            )
        return cls(base_url=base_url.rstrip("/"), api_key=api_key, model=model, timeout_s=timeout_s)


class LLMRequestError(RuntimeError):
    def __init__(self, status_code: int, body: str) -> None:
        super().__init__(f"LLM request failed: HTTP {status_code} {body}")
        self.status_code = status_code
        self.body = body


class OpenAICompatibleLLMClient:
    def __init__(self, config: LLMConfig) -> None:
        self.config = config

    def chat(self, messages: list[dict], temperature: float = 0.0, max_tokens: int = 256) -> dict:
        url = f"{self.config.base_url}/chat/completions"
        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=self.config.timeout_s) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise LLMRequestError(exc.code, body) from exc

    def list_models(self) -> dict:
        url = f"{self.config.base_url}/models"
        req = urllib.request.Request(
            url,
            method="GET",
            headers={"Authorization": f"Bearer {self.config.api_key}"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self.config.timeout_s) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise LLMRequestError(exc.code, body) from exc

    def smoke_test(self) -> dict:
        models_response = self.list_models()
        available_models = [item.get("id", "") for item in models_response.get("data", []) if item.get("id")]
        candidate_models = [self.config.model, "moonshot-v1-auto", "moonshot-v1-8k"]
        for model_id in available_models[:3]:
            if model_id not in candidate_models:
                candidate_models.append(model_id)

        last_error: LLMRequestError | None = None
        for model in candidate_models:
            if not model:
                continue
            for attempt in range(3):
                try:
                    response = self.chat(
                        messages=[
                            {"role": "system", "content": "You are a concise API smoke-test assistant."},
                            {"role": "user", "content": "Reply with exactly: BELIEFSYNC_OK"},
                        ],
                        temperature=0.0,
                        max_tokens=8,
                    ) if model == self.config.model else self._chat_with_model(model)
                    response["_beliefsync_model_used"] = model
                    response["_beliefsync_models_count"] = len(available_models)
                    return response
                except LLMRequestError as exc:
                    last_error = exc
                    if exc.status_code == 429 and attempt < 2:
                        time.sleep(1 + attempt)
                        continue
                    break

        if last_error is not None:
            raise last_error
        raise RuntimeError("Smoke test failed before any model request was attempted.")

    def _chat_with_model(self, model: str) -> dict:
        url = f"{self.config.base_url}/chat/completions"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a concise API smoke-test assistant."},
                {"role": "user", "content": "Reply with exactly: BELIEFSYNC_OK"},
            ],
            "temperature": 0.0,
            "max_tokens": 8,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=self.config.timeout_s) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise LLMRequestError(exc.code, body) from exc

    def extract_candidate_beliefs(
        self,
        repo_id: str,
        issue_text: str,
        test_log_text: str,
        issue_id: str = "",
        commit_hash: str = "",
    ) -> list[Belief]:
        prompt = {
            "role": "user",
            "content": (
                "Extract up to 5 repository-state beliefs for a coding agent.\n"
                "Return strict JSON only as a list.\n"
                "Each item must contain: belief_type, claim, file_paths, symbols, related_tests, importance_score, confidence.\n"
                "Valid belief_type values: bug_localization, api_contract, test_expectation, requirement, dependency.\n"
                "Issue:\n"
                f"{issue_text}\n\n"
                "Test log:\n"
                f"{test_log_text}\n"
            ),
        }
        response = self.chat(
            messages=[
                {"role": "system", "content": "You extract compact structured repository-state beliefs for coding agents."},
                prompt,
            ],
            temperature=0.0,
            max_tokens=800,
        )
        content = response["choices"][0]["message"]["content"]
        payload = _parse_json_payload(content)
        beliefs: list[Belief] = []
        for idx, item in enumerate(payload, start=1):
            belief_type = BeliefType(item["belief_type"])
            confidence = _normalize_unit_score(item.get("confidence", 0.6))
            importance_score = _normalize_unit_score(item.get("importance_score", 0.7))
            beliefs.append(
                Belief(
                    belief_id=f"llm-belief-{idx}",
                    belief_type=belief_type,
                    claim=item["claim"].strip(),
                    scope=Scope(
                        repository_id=repo_id,
                        commit_hash=commit_hash,
                        file_paths=item.get("file_paths", []),
                        symbols=item.get("symbols", []),
                        related_tests=item.get("related_tests", []),
                        issue_id=issue_id,
                    ),
                    evidence=[
                        EvidenceRef(
                            evidence_type=EvidenceType.ISSUE_TEXT,
                            location=str(issue_id or "issue"),
                            content_snippet=issue_text[:220],
                            source_version=commit_hash,
                        ),
                        EvidenceRef(
                            evidence_type=EvidenceType.TEST_LOG,
                            location="test_log",
                            content_snippet=test_log_text[:220],
                            source_version=commit_hash,
                        ),
                    ],
                    version_validity=VersionValidity(
                        created_from_commit=commit_hash,
                        last_confirmed_commit=commit_hash,
                    ),
                    confidence=confidence,
                    importance_score=importance_score,
                    invalidation_triggers=["code_diff", "test_changed", "issue_updated", "comment_updated"],
                )
            )
        return beliefs


def _parse_json_payload(text: str):
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`")
        if stripped.startswith("json"):
            stripped = stripped[4:].strip()
    return json.loads(stripped)


def _normalize_unit_score(value) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return 0.5
    if score > 1.0:
        if score <= 10.0:
            score = score / 10.0
        elif score <= 100.0:
            score = score / 100.0
        else:
            score = 1.0
    return max(0.0, min(1.0, score))


def load_text(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")
