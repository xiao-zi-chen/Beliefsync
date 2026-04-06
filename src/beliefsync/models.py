from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class BeliefType(str, Enum):
    BUG_LOCALIZATION = "bug_localization"
    API_CONTRACT = "api_contract"
    TEST_EXPECTATION = "test_expectation"
    REQUIREMENT = "requirement"
    DEPENDENCY = "dependency"


class BeliefStatus(str, Enum):
    ACTIVE = "active"
    STALE_SUSPECTED = "stale_suspected"
    INVALIDATED = "invalidated"
    REVALIDATED = "revalidated"


class EvidenceType(str, Enum):
    ISSUE_TEXT = "issue_text"
    TEST_LOG = "test_log"
    CODE_SPAN = "code_span"
    COMMENT = "comment"
    EXECUTION_TRACE = "execution_trace"


class EventType(str, Enum):
    CODE_DIFF = "code_diff"
    TEST_CHANGED = "test_changed"
    ISSUE_UPDATED = "issue_updated"
    COMMENT_UPDATED = "comment_updated"
    DEPENDENCY_BUMPED = "dependency_bumped"
    EXECUTION_CONFLICT = "execution_conflict"


class ActionType(str, Enum):
    READ_FILE = "read_file"
    RUN_TARGETED_TEST = "run_targeted_test"
    READ_ISSUE_COMMENT = "read_issue_comment"
    SEARCH_SYMBOL = "search_symbol"
    INSPECT_DEPENDENCY = "inspect_dependency"
    REPRODUCE_FAILURE = "reproduce_failure"
    DISCARD_BELIEF = "discard_belief"


@dataclass
class Scope:
    repository_id: str
    branch: str = "main"
    commit_hash: str = ""
    file_paths: list[str] = field(default_factory=list)
    symbols: list[str] = field(default_factory=list)
    related_tests: list[str] = field(default_factory=list)
    issue_id: str = ""


@dataclass
class EvidenceRef:
    evidence_type: EvidenceType
    location: str
    content_snippet: str
    source_version: str = ""
    support_polarity: str = "supports"


@dataclass
class VersionValidity:
    created_from_commit: str = ""
    last_confirmed_commit: str = ""
    invalid_after_commits: list[str] = field(default_factory=list)
    valid_under_issue_state_ids: list[str] = field(default_factory=list)


@dataclass
class Belief:
    belief_id: str
    belief_type: BeliefType
    claim: str
    scope: Scope
    evidence: list[EvidenceRef] = field(default_factory=list)
    version_validity: VersionValidity = field(default_factory=VersionValidity)
    confidence: float = 0.5
    status: BeliefStatus = BeliefStatus.ACTIVE
    invalidation_triggers: list[str] = field(default_factory=list)
    importance_score: float = 0.5
    last_verified_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ChangeEvent:
    event_id: str
    event_type: EventType
    summary: str
    paths: list[str] = field(default_factory=list)
    symbols: list[str] = field(default_factory=list)
    commit_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class StaleBeliefAssessment:
    belief_id: str
    stale_probability: float
    reasons: list[str] = field(default_factory=list)
    impacted_paths: list[str] = field(default_factory=list)
    impacted_symbols: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RevalidationAction:
    action_type: ActionType
    target: str
    rationale: str
    estimated_cost: float
    expected_value: float
    source_belief_ids: list[str] = field(default_factory=list)

    def score(self) -> float:
        return self.expected_value - self.estimated_cost

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AnalysisReport:
    beliefs: list[Belief]
    assessments: list[StaleBeliefAssessment]
    actions: list[RevalidationAction]

    def to_dict(self) -> dict[str, Any]:
        return {
            "beliefs": [belief.to_dict() for belief in self.beliefs],
            "assessments": [assessment.to_dict() for assessment in self.assessments],
            "actions": [action.to_dict() for action in self.actions],
        }
