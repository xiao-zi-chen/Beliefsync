from __future__ import annotations

from .models import Belief, BeliefStatus, ChangeEvent, EventType, StaleBeliefAssessment


class RuleBasedStaleBeliefDetector:
    """Transparent baseline for scoring stale beliefs from repository events."""

    def assess(self, beliefs: list[Belief], events: list[ChangeEvent]) -> list[StaleBeliefAssessment]:
        assessments: list[StaleBeliefAssessment] = []
        for belief in beliefs:
            probability = 0.0
            reasons: list[str] = []
            impacted_paths: list[str] = []
            impacted_symbols: list[str] = []

            for event in events:
                overlap_paths = set(belief.scope.file_paths) & set(event.paths)
                overlap_symbols = set(belief.scope.symbols) & set(event.symbols)
                overlap_tests = set(belief.scope.related_tests) & set(event.paths + event.symbols)

                if overlap_paths:
                    probability += 0.45
                    reasons.append(f"path overlap with {event.event_type.value}")
                    impacted_paths.extend(sorted(overlap_paths))

                if overlap_symbols:
                    probability += 0.25
                    reasons.append(f"symbol overlap with {event.event_type.value}")
                    impacted_symbols.extend(sorted(overlap_symbols))

                if overlap_tests:
                    probability += 0.2
                    reasons.append(f"test overlap with {event.event_type.value}")

                if event.event_type == EventType.TEST_CHANGED and belief.belief_type.value == "test_expectation":
                    probability += 0.25
                    reasons.append("test expectation likely changed")

                if event.event_type in (EventType.ISSUE_UPDATED, EventType.COMMENT_UPDATED) and belief.belief_type.value in (
                    "requirement",
                    "api_contract",
                    "test_expectation",
                ):
                    probability += 0.2
                    reasons.append("requirement-facing belief may have changed")

                if event.event_type == EventType.CODE_DIFF and belief.belief_type.value in ("bug_localization", "api_contract"):
                    probability += 0.15
                    reasons.append("implementation-facing belief may have drifted")

            probability = max(0.0, min(1.0, probability * belief.importance_score))
            if probability >= 0.5:
                belief.status = BeliefStatus.STALE_SUSPECTED

            assessments.append(
                StaleBeliefAssessment(
                    belief_id=belief.belief_id,
                    stale_probability=round(probability, 3),
                    reasons=self._dedupe(reasons),
                    impacted_paths=self._dedupe(impacted_paths),
                    impacted_symbols=self._dedupe(impacted_symbols),
                )
            )

        return sorted(assessments, key=lambda x: x.stale_probability, reverse=True)

    def _dedupe(self, values: list[str]) -> list[str]:
        ordered: list[str] = []
        for value in values:
            if value not in ordered:
                ordered.append(value)
        return ordered
