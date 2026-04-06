import json
import tempfile
import unittest
from pathlib import Path

from beliefsync.config import BeliefSyncConfig
from beliefsync.workspace import default_scan_output_dir, discover_workspace, init_workspace, load_workspace_config


class WorkspaceTests(unittest.TestCase):
    def test_workspace_init_and_discovery(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir) / "repo"
            repo.mkdir()
            workspace = init_workspace(repo, BeliefSyncConfig(repo_id="demo/repo"))
            discovered = discover_workspace(repo)
            self.assertEqual(workspace, discovered)

            config = load_workspace_config(repo)
            self.assertIsNotNone(config)
            self.assertEqual(config.repo_id, "demo/repo")

    def test_default_scan_output_dir_uses_workspace_reports(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir) / "repo"
            repo.mkdir()
            init_workspace(repo, BeliefSyncConfig(repo_id="demo/repo"))
            output_dir = default_scan_output_dir(repo)
            self.assertIn(".beliefsync", str(output_dir))
            self.assertEqual(output_dir.parent.name, "reports")


if __name__ == "__main__":
    unittest.main()
