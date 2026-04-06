import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CLIWorkflowTests(unittest.TestCase):
    def test_snapshot_and_refresh_workflow(self):
        if shutil.which("git") is None:
            self.skipTest("git is not available")

        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir) / "repo"
            repo.mkdir()
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True, capture_output=True)

            src_dir = repo / "src"
            src_dir.mkdir()
            target = src_dir / "retry_manager.py"
            target.write_text("def foo():\n    return 1\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True, capture_output=True)

            issue_file = repo / "issue.md"
            issue_file.write_text("# Issue\n\n`RetryManager` should reset state.\n", encoding="utf-8")
            test_log = repo / "failing_tests.txt"
            test_log.write_text("FAILED tests/test_retry.py::test_retry_resets_state\n", encoding="utf-8")

            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "beliefsync",
                    "snapshot",
                    "--repo-id",
                    "demo/repo",
                    "--repo-path",
                    str(repo),
                    "--issue-file",
                    str(issue_file),
                    "--test-log",
                    str(test_log),
                ],
                cwd=repo,
                check=True,
                capture_output=True,
                text=True,
            )

            target.write_text("def foo():\n    return 2\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", "update"], cwd=repo, check=True, capture_output=True)

            refresh = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "beliefsync",
                    "refresh",
                    "--repo-path",
                    str(repo),
                    "--head-ref",
                    "HEAD",
                ],
                cwd=repo,
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertIn("Saved refreshed artifacts", refresh.stdout)
            reports_dir = repo / ".beliefsync" / "reports"
            self.assertTrue(reports_dir.exists())
            report_dirs = [path for path in reports_dir.iterdir() if path.is_dir()]
            self.assertGreaterEqual(len(report_dirs), 1)


if __name__ == "__main__":
    unittest.main()
