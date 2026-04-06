from __future__ import annotations

from .models import ActionType, Belief, BeliefType, RevalidationAction, StaleBeliefAssessment


class CostAwareRevalidationPlanner:
    """Convert stale-belief assessments into targeted, ranked recovery actions."""

    def plan(self, beliefs: list[Belief], assessments: list[StaleBeliefAssessment]) -> list[RevalidationAction]:
        belief_map = {belief.belief_id: belief for belief in beliefs}
        actions: list[RevalidationAction] = []

        for assessment in assessments:
            belief = belief_map.get(assessment.belief_id)
            if belief is None or assessment.stale_probability < 0.3:
                continue

            if belief.scope.related_tests:
                for test_name in belief.scope.related_tests[:1]:
                    actions.append(
                        RevalidationAction(
                            action_type=ActionType.RUN_TARGETED_TEST,
                            target=test_name,
                            rationale=f"Re-run the most relevant test for {belief.belief_id}.",
                            estimated_cost=0.45,
                            expected_value=assessment.stale_probability * belief.importance_score + 0.35,
                            source_belief_ids=[belief.belief_id],
                        )
                    )

            if belief.scope.file_paths:
                actions.append(
                    RevalidationAction(
                        action_type=ActionType.READ_FILE,
                        target=belief.scope.file_paths[0],
                        rationale=f"Inspect the primary affected file for {belief.belief_id}.",
                        estimated_cost=0.2,
                        expected_value=assessment.stale_probability * belief.importance_score + 0.18,
                        source_belief_ids=[belief.belief_id],
                    )
                )

            if belief.scope.symbols:
                actions.append(
                    RevalidationAction(
                        action_type=ActionType.SEARCH_SYMBOL,
                        target=belief.scope.symbols[0],
                        rationale=f"Re-check symbol-level behavior for {belief.belief_id}.",
                        estimated_cost=0.15,
                        expected_value=assessment.stale_probability * 0.75 + 0.2,
                        source_belief_ids=[belief.belief_id],
                    )
                )

            if belief.belief_type in (BeliefType.REQUIREMENT, BeliefType.API_CONTRACT, BeliefType.TEST_EXPECTATION):
                actions.append(
                    RevalidationAction(
                        action_type=ActionType.READ_ISSUE_COMMENT,
                        target=belief.scope.issue_id or "latest-comment",
                        rationale=f"Check whether issue requirements changed for {belief.belief_id}.",
                        estimated_cost=0.1,
                        expected_value=assessment.stale_probability * 0.6 + 0.15,
                        source_belief_ids=[belief.belief_id],
                    )
                )

        return self._merge_and_rank(actions)

    def _merge_and_rank(self, actions: list[RevalidationAction]) -> list[RevalidationAction]:
        merged: dict[tuple[str, str], RevalidationAction] = {}
        for action in actions:
            key = (action.action_type.value, action.target)
            if key not in merged:
                merged[key] = action
                continue
            existing = merged[key]
            existing.expected_value = max(existing.expected_value, action.expected_value)
            existing.source_belief_ids = sorted(set(existing.source_belief_ids + action.source_belief_ids))

        return sorted(merged.values(), key=lambda action: action.score(), reverse=True)
