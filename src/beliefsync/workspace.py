from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from .config import BeliefSyncConfig, load_config, save_config


@dataclass
class WorkspaceState:
    repo_id: str = "unknown/repo"
    repo_path: str = ""
    last_base_ref: str = ""
    last_head_ref: str = ""
    issue_file: str = ""
    test_log_file: str = ""
    issue_id: str = ""
    beliefs_file: str = ""
    last_report_dir: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def init_workspace(path: str | Path, config: BeliefSyncConfig | None = None) -> Path:
    root = Path(path).resolve()
    workspace = root / ".beliefsync"
    workspace.mkdir(parents=True, exist_ok=True)

    config = config or BeliefSyncConfig()
    save_config(workspace / "config.json", config)
    (workspace / "README.md").write_text(
        "# BeliefSync Workspace\n\nThis directory stores local belief snapshots, configs, and analysis reports.\n",
        encoding="utf-8",
    )
    (workspace / ".gitignore").write_text("reports/\ncache/\n", encoding="utf-8")
    (workspace / "reports").mkdir(exist_ok=True)
    (workspace / "cache").mkdir(exist_ok=True)
    save_workspace_state(workspace / "state.json", WorkspaceState(repo_id=config.repo_id))
    return workspace


def discover_workspace(path: str | Path = ".") -> Path | None:
    current = Path(path).resolve()
    candidates = [current, *current.parents]
    for candidate in candidates:
        workspace = candidate / ".beliefsync"
        if workspace.exists() and workspace.is_dir():
            return workspace
    return None


def load_workspace_config(path: str | Path = ".") -> BeliefSyncConfig | None:
    workspace = discover_workspace(path)
    if workspace is None:
        return None
    config_path = workspace / "config.json"
    if not config_path.exists():
        return None
    return load_config(config_path)


def default_scan_output_dir(path: str | Path = ".") -> Path:
    workspace = discover_workspace(path)
    if workspace is None:
        workspace = init_workspace(path)
    reports_dir = workspace / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("scan-%Y%m%d-%H%M%S")
    return reports_dir / timestamp


def save_workspace_state(path: str | Path, state: WorkspaceState) -> None:
    Path(path).write_text(json.dumps(state.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")


def load_workspace_state(path: str | Path = ".") -> WorkspaceState | None:
    workspace = discover_workspace(path)
    if workspace is None:
        return None
    state_path = workspace / "state.json"
    if not state_path.exists():
        return None
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    return WorkspaceState(**payload)
