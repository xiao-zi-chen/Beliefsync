from __future__ import annotations

import re
import subprocess
from pathlib import Path

from .config import BeliefSyncConfig
from .models import ChangeEvent, EventType


class GitEventExtractor:
    def __init__(self, config: BeliefSyncConfig | None = None) -> None:
        self.config = config or BeliefSyncConfig()

    def events_between(self, repo_path: str | Path, base_ref: str, head_ref: str) -> list[ChangeEvent]:
        repo = Path(repo_path).resolve()
        changed_files = self._run_git(repo, ["diff", "--name-only", base_ref, head_ref]).splitlines()
        diff_text = self._run_git(repo, ["diff", "--unified=0", base_ref, head_ref])
        symbols_by_path = self._extract_symbols_by_path(diff_text)

        events: list[ChangeEvent] = []
        for index, raw_path in enumerate(changed_files, start=1):
            path = raw_path.strip()
            if not path:
                continue
            event_type = self._infer_event_type(path)
            events.append(
                ChangeEvent(
                    event_id=f"git-{index}",
                    event_type=event_type,
                    summary=f"Changed {path} between {base_ref} and {head_ref}",
                    paths=[path],
                    symbols=symbols_by_path.get(path, []),
                    commit_hash=head_ref,
                )
            )
        return events

    def current_head(self, repo_path: str | Path) -> str:
        repo = Path(repo_path).resolve()
        return self._run_git(repo, ["rev-parse", "HEAD"]).strip()

    def _infer_event_type(self, path: str) -> EventType:
        normalized = path.replace("\\", "/")
        if any(marker in normalized for marker in self.config.test_path_markers):
            return EventType.TEST_CHANGED
        if self.config.track_dependency_files:
            for pattern in self.config.dependency_file_patterns:
                if normalized.endswith(pattern):
                    return EventType.DEPENDENCY_BUMPED
        return EventType.CODE_DIFF

    def _extract_symbols_by_path(self, diff_text: str) -> dict[str, list[str]]:
        current_path = ""
        symbols: dict[str, list[str]] = {}
        for line in diff_text.splitlines():
            if line.startswith("+++ b/"):
                current_path = line[6:].strip()
                symbols.setdefault(current_path, [])
                continue
            if not current_path:
                continue
            if line.startswith("@@"):
                for symbol in re.findall(r"([A-Za-z_][A-Za-z0-9_]*)", line):
                    if symbol not in symbols[current_path] and symbol not in {"if", "for", "while", "return"}:
                        symbols[current_path].append(symbol)
            elif line.startswith("+") or line.startswith("-"):
                for symbol in re.findall(r"\b(?:def|class|function)\s+([A-Za-z_][A-Za-z0-9_]*)", line):
                    if symbol not in symbols[current_path]:
                        symbols[current_path].append(symbol)
        return symbols

    def _run_git(self, repo: Path, args: list[str]) -> str:
        result = subprocess.run(
            ["git", *args],
            cwd=repo,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout
