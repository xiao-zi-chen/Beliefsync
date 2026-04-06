import tempfile
import unittest
from pathlib import Path

from beliefsync.engine import BeliefSyncEngine
from beliefsync.store import save_beliefs


class EngineTests(unittest.TestCase):
    def test_engine_builds_report(self):
        engine = BeliefSyncEngine()
        issue_file = Path("examples/demo_issue.md")
        test_file = Path("examples/demo_test_log.txt")
        events_file = Path("examples/demo_events.json")
        beliefs = engine.extract_from_files(
            repo_id="demo/repo",
            issue_file=issue_file,
            test_log_file=test_file,
            commit_hash="base",
            issue_id="issue-1",
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            belief_file = Path(tmpdir) / "beliefs.json"
            save_beliefs(belief_file, beliefs)
            report = engine.analyze_from_files(belief_file, events_file)
            self.assertGreater(len(report.assessments), 0)
            self.assertGreater(len(report.actions), 0)
            payload = report.to_dict()
            self.assertIn("beliefs", payload)
            self.assertIn("assessments", payload)
            self.assertIn("actions", payload)


if __name__ == "__main__":
    unittest.main()
