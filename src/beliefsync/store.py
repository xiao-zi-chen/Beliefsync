from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import (
    ActionType,
    AnalysisReport,
    Belief,
    BeliefStatus,
    BeliefType,
    ChangeEvent,
    EvidenceRef,
    EvidenceType,
    EventType,
    RevalidationAction,
    Scope,
    StaleBeliefAssessment,
    VersionValidity,
)


def _belief_from_dict(data: dict[str, Any]) -> Belief:
    return Belief(
        belief_id=data["belief_id"],
        belief_type=BeliefType(data["belief_type"]),
        claim=data["claim"],
        scope=Scope(**data["scope"]),
        evidence=[
            EvidenceRef(
                evidence_type=EvidenceType(e["evidence_type"]),
                location=e["location"],
                content_snippet=e["content_snippet"],
                source_version=e.get("source_version", ""),
                support_polarity=e.get("support_polarity", "supports"),
            )
            for e in data.get("evidence", [])
        ],
        version_validity=VersionValidity(**data.get("version_validity", {})),
        confidence=data.get("confidence", 0.5),
        status=BeliefStatus(data.get("status", BeliefStatus.ACTIVE.value)),
        invalidation_triggers=data.get("invalidation_triggers", []),
        importance_score=data.get("importance_score", 0.5),
        last_verified_at=data.get("last_verified_at", ""),
    )


def _event_from_dict(data: dict[str, Any]) -> ChangeEvent:
    return ChangeEvent(
        event_id=data["event_id"],
        event_type=EventType(data["event_type"]),
        summary=data["summary"],
        paths=data.get("paths", []),
        symbols=data.get("symbols", []),
        commit_hash=data.get("commit_hash", ""),
    )


def load_beliefs(path: str | Path) -> list[Belief]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return [_belief_from_dict(item) for item in payload]


def save_beliefs(path: str | Path, beliefs: list[Belief]) -> None:
    Path(path).write_text(
        json.dumps([belief.to_dict() for belief in beliefs], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def load_events(path: str | Path) -> list[ChangeEvent]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return [_event_from_dict(item) for item in payload]


def save_report(path: str | Path, report: AnalysisReport) -> None:
    Path(path).write_text(
        json.dumps(report.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def save_assessments(path: str | Path, assessments: list[StaleBeliefAssessment]) -> None:
    Path(path).write_text(
        json.dumps([item.to_dict() for item in assessments], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def save_actions(path: str | Path, actions: list[RevalidationAction]) -> None:
    Path(path).write_text(
        json.dumps([item.to_dict() for item in actions], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def load_actions(path: str | Path) -> list[RevalidationAction]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return [
        RevalidationAction(
            action_type=ActionType(item["action_type"]),
            target=item["target"],
            rationale=item["rationale"],
            estimated_cost=item["estimated_cost"],
            expected_value=item["expected_value"],
            source_belief_ids=item.get("source_belief_ids", []),
        )
        for item in payload
    ]
