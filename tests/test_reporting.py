import unittest

from beliefsync.extractors import HeuristicBeliefExtractor
from beliefsync.models import ChangeEvent, EventType
from beliefsync.models import AnalysisReport
from beliefsync.detector import RuleBasedStaleBeliefDetector
from beliefsync.planner import CostAwareRevalidationPlanner
from beliefsync.reporting import ReportRenderer


class ReportingTests(unittest.TestCase):
    def test_markdown_report_contains_expected_sections(self):
        extractor = HeuristicBeliefExtractor()
        beliefs = extractor.extract(
            repo_id="demo/repo",
            issue_text="`RetryManager` in src/retry_manager.py should reset state",
            test_log_text="FAILED tests/test_retry.py::test_retry_resets_state",
        )
        events = [
            ChangeEvent(
                event_id="evt-1",
                event_type=EventType.CODE_DIFF,
                summary="changed retry manager",
                paths=["src/retry_manager.py"],
                symbols=["RetryManager"],
                commit_hash="abc",
            )
        ]
        detector = RuleBasedStaleBeliefDetector()
        planner = CostAwareRevalidationPlanner()
        assessments = detector.assess(beliefs, events)
        actions = planner.plan(beliefs, assessments)
        report = AnalysisReport(beliefs=beliefs, assessments=assessments, actions=actions)
        renderer = ReportRenderer()
        markdown = renderer.render_markdown(report)
        self.assertIn("# BeliefSync Report", markdown)
        self.assertIn("## Summary", markdown)
        self.assertIn("## Recommended Actions", markdown)


if __name__ == "__main__":
    unittest.main()
