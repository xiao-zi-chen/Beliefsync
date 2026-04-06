from __future__ import annotations

from pathlib import Path

from .config import BeliefSyncConfig
from .detector import RuleBasedStaleBeliefDetector
from .extractors import HeuristicBeliefExtractor
from .models import AnalysisReport
from .planner import CostAwareRevalidationPlanner
from .repo_events import GitEventExtractor
from .store import load_beliefs, load_events


class BeliefSyncEngine:
    def __init__(self, config: BeliefSyncConfig | None = None) -> None:
        self.config = config or BeliefSyncConfig()
        self.extractor = HeuristicBeliefExtractor()
        self.detector = RuleBasedStaleBeliefDetector()
        self.planner = CostAwareRevalidationPlanner()
        self.git_events = GitEventExtractor(self.config)

    def extract_from_files(
        self,
        repo_id: str,
        issue_file: str | Path,
        test_log_file: str | Path,
        commit_hash: str = "",
        issue_id: str = "",
    ):
        return self.extractor.extract_from_files(
            repo_id=repo_id,
            issue_file=issue_file,
            test_log_file=test_log_file,
            commit_hash=commit_hash,
            issue_id=issue_id,
        )

    def analyze_from_files(self, beliefs_file: str | Path, events_file: str | Path) -> AnalysisReport:
        beliefs = load_beliefs(beliefs_file)
        events = load_events(events_file)
        assessments = self.detector.assess(beliefs, events)
        actions = self.planner.plan(beliefs, assessments)[: self.config.max_actions]
        return AnalysisReport(beliefs=beliefs, assessments=assessments, actions=actions)

    def analyze_from_objects(self, beliefs, events) -> AnalysisReport:
        assessments = self.detector.assess(beliefs, events)
        actions = self.planner.plan(beliefs, assessments)[: self.config.max_actions]
        return AnalysisReport(beliefs=beliefs, assessments=assessments, actions=actions)

    def ingest_git_events(self, repo_path: str | Path, base_ref: str, head_ref: str):
        return self.git_events.events_between(repo_path, base_ref, head_ref)
