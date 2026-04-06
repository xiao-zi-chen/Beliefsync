import unittest

from beliefsync.detector import RuleBasedStaleBeliefDetector
from beliefsync.extractors import HeuristicBeliefExtractor
from beliefsync.models import ChangeEvent, EventType


class DetectorTests(unittest.TestCase):
    def test_detector_marks_path_overlap_as_stale(self):
        extractor = HeuristicBeliefExtractor()
        beliefs = extractor.extract(
            repo_id="demo/repo",
            issue_text="RetryManager should reset `retry_count` in src/retry_manager.py",
            test_log_text="FAILED tests/test_retry.py::test_retry_resets_state",
            commit_hash="abc",
        )
        detector = RuleBasedStaleBeliefDetector()
        events = [
            ChangeEvent(
                event_id="1",
                event_type=EventType.CODE_DIFF,
                summary="changed file",
                paths=["src/retry_manager.py"],
                symbols=["RetryManager"],
                commit_hash="def",
            )
        ]
        assessments = detector.assess(beliefs, events)
        self.assertTrue(any(item.stale_probability > 0.5 for item in assessments))


if __name__ == "__main__":
    unittest.main()
