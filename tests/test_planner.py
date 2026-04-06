import unittest

from beliefsync.extractors import HeuristicBeliefExtractor
from beliefsync.models import StaleBeliefAssessment
from beliefsync.planner import CostAwareRevalidationPlanner


class PlannerTests(unittest.TestCase):
    def test_planner_produces_actions(self):
        extractor = HeuristicBeliefExtractor()
        beliefs = extractor.extract(
            repo_id="demo/repo",
            issue_text="`RetryManager` state reset in src/retry_manager.py",
            test_log_text="FAILED tests/test_retry.py::test_retry_resets_state",
        )
        planner = CostAwareRevalidationPlanner()
        assessments = [
            StaleBeliefAssessment(
                belief_id=beliefs[0].belief_id,
                stale_probability=0.8,
                reasons=["path overlap"],
                impacted_paths=["src/retry_manager.py"],
                impacted_symbols=["RetryManager"],
            )
        ]
        actions = planner.plan(beliefs, assessments)
        self.assertGreater(len(actions), 0)
        self.assertEqual(actions[0].source_belief_ids, [beliefs[0].belief_id])


if __name__ == "__main__":
    unittest.main()
