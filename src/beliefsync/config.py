from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class BeliefSyncConfig:
    repo_id: str = "unknown/repo"
    branch: str = "main"
    stale_threshold: float = 0.5
    max_actions: int = 5
    track_dependency_files: bool = True
    dependency_file_patterns: list[str] = field(
        default_factory=lambda: [
            "requirements.txt",
            "poetry.lock",
            "package.json",
            "package-lock.json",
            "pnpm-lock.yaml",
            "Cargo.lock",
            "go.mod",
            "pom.xml",
        ]
    )
    test_path_markers: list[str] = field(default_factory=lambda: ["tests/", "test_"])

    def to_dict(self) -> dict:
        return asdict(self)


def save_config(path: str | Path, config: BeliefSyncConfig) -> None:
    Path(path).write_text(json.dumps(config.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")


def load_config(path: str | Path) -> BeliefSyncConfig:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return BeliefSyncConfig(**payload)
