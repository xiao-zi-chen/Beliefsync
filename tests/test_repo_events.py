import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from beliefsync.repo_events import GitEventExtractor


class RepoEventTests(unittest.TestCase):
    def test_git_event_extractor_reads_diff(self):
        if shutil.which("git") is None:
            self.skipTest("git is not available")

        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True, capture_output=True)

            file_path = repo / "src_file.py"
            file_path.write_text("def foo():\n    return 1\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True, capture_output=True)

            file_path.write_text("def foo():\n    return 2\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", "update"], cwd=repo, check=True, capture_output=True)

            extractor = GitEventExtractor()
            events = extractor.events_between(repo, "HEAD~1", "HEAD")
            self.assertGreater(len(events), 0)
            self.assertEqual(events[0].paths[0], "src_file.py")


if __name__ == "__main__":
    unittest.main()
