from __future__ import annotations

import re
from pathlib import Path

from .models import Belief, BeliefType, EvidenceRef, EvidenceType, Scope, VersionValidity


class HeuristicBeliefExtractor:
    """Transparent baseline extractor that turns issue text and test logs into beliefs."""

    def extract_from_files(
        self,
        repo_id: str,
        issue_file: str | Path,
        test_log_file: str | Path,
        commit_hash: str = "",
        issue_id: str = "",
    ) -> list[Belief]:
        issue_text = Path(issue_file).read_text(encoding="utf-8")
        test_log_text = Path(test_log_file).read_text(encoding="utf-8")
        return self.extract(repo_id, issue_text, test_log_text, commit_hash=commit_hash, issue_id=issue_id)

    def extract(
        self,
        repo_id: str,
        issue_text: str,
        test_log_text: str,
        commit_hash: str = "",
        issue_id: str = "",
    ) -> list[Belief]:
        beliefs: list[Belief] = []
        symbols = self._extract_symbols(issue_text + "\n" + test_log_text)
        files = self._extract_paths(issue_text + "\n" + test_log_text)
        tests = self._extract_tests(test_log_text)

        if files or symbols:
            beliefs.append(
                Belief(
                    belief_id="belief-localization-1",
                    belief_type=BeliefType.BUG_LOCALIZATION,
                    claim="The issue is likely localized in the identified files or symbols.",
                    scope=Scope(
                        repository_id=repo_id,
                        commit_hash=commit_hash,
                        file_paths=files,
                        symbols=symbols,
                        related_tests=tests,
                        issue_id=issue_id,
                    ),
                    evidence=[
                        EvidenceRef(
                            evidence_type=EvidenceType.ISSUE_TEXT,
                            location=str(issue_id or "issue"),
                            content_snippet=issue_text[:180],
                            source_version=commit_hash,
                        ),
                        EvidenceRef(
                            evidence_type=EvidenceType.TEST_LOG,
                            location="test_log",
                            content_snippet=test_log_text[:180],
                            source_version=commit_hash,
                        ),
                    ],
                    version_validity=VersionValidity(
                        created_from_commit=commit_hash,
                        last_confirmed_commit=commit_hash,
                    ),
                    confidence=0.72,
                    invalidation_triggers=["code_diff", "test_changed"],
                    importance_score=0.9,
                )
            )

        if tests:
            beliefs.append(
                Belief(
                    belief_id="belief-test-expectation-1",
                    belief_type=BeliefType.TEST_EXPECTATION,
                    claim="The failing tests encode the current behavior requirement for retry state reset.",
                    scope=Scope(
                        repository_id=repo_id,
                        commit_hash=commit_hash,
                        file_paths=[],
                        symbols=symbols,
                        related_tests=tests,
                        issue_id=issue_id,
                    ),
                    evidence=[
                        EvidenceRef(
                            evidence_type=EvidenceType.TEST_LOG,
                            location="test_log",
                            content_snippet=test_log_text[:220],
                            source_version=commit_hash,
                        )
                    ],
                    version_validity=VersionValidity(
                        created_from_commit=commit_hash,
                        last_confirmed_commit=commit_hash,
                    ),
                    confidence=0.8,
                    invalidation_triggers=["test_changed", "issue_updated"],
                    importance_score=0.95,
                )
            )

        if symbols:
            beliefs.append(
                Belief(
                    belief_id="belief-api-contract-1",
                    belief_type=BeliefType.API_CONTRACT,
                    claim="The retry cycle should reset transient state before incrementing or reusing previous attempt counters.",
                    scope=Scope(
                        repository_id=repo_id,
                        commit_hash=commit_hash,
                        file_paths=files,
                        symbols=symbols,
                        related_tests=tests,
                        issue_id=issue_id,
                    ),
                    evidence=[
                        EvidenceRef(
                            evidence_type=EvidenceType.ISSUE_TEXT,
                            location="issue",
                            content_snippet=issue_text[:220],
                            source_version=commit_hash,
                        )
                    ],
                    version_validity=VersionValidity(
                        created_from_commit=commit_hash,
                        last_confirmed_commit=commit_hash,
                    ),
                    confidence=0.68,
                    invalidation_triggers=["code_diff", "comment_updated", "issue_updated"],
                    importance_score=0.88,
                )
            )

        return beliefs

    def _extract_symbols(self, text: str) -> list[str]:
        backticked = re.findall(r"`([A-Za-z_][A-Za-z0-9_]*)`", text)
        method_like = re.findall(r"\b([A-Z][A-Za-z0-9_]*|[a-z_][A-Za-z0-9_]*)(?=\()", text)
        ordered: list[str] = []
        for symbol in backticked + method_like:
            if symbol not in ordered:
                ordered.append(symbol)
        return ordered[:8]

    def _extract_paths(self, text: str) -> list[str]:
        matches = re.findall(r"([A-Za-z0-9_./-]+\.(?:py|ts|js|java|go|rs))", text)
        ordered: list[str] = []
        for path in matches:
            if path not in ordered:
                ordered.append(path)
        return ordered[:8]

    def _extract_tests(self, text: str) -> list[str]:
        matches = re.findall(r"(tests/[A-Za-z0-9_./-]+::[A-Za-z0-9_]+)", text)
        ordered: list[str] = []
        for test_name in matches:
            if test_name not in ordered:
                ordered.append(test_name)
        return ordered[:8]
