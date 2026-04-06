from __future__ import annotations

from dataclasses import dataclass, field

from .models import Belief, ChangeEvent


@dataclass
class ValidationIssue:
    level: str
    message: str
    object_id: str = ""


@dataclass
class ValidationReport:
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not any(issue.level == "error" for issue in self.issues)

    def add(self, level: str, message: str, object_id: str = "") -> None:
        self.issues.append(ValidationIssue(level=level, message=message, object_id=object_id))


def validate_beliefs(beliefs: list[Belief]) -> ValidationReport:
    report = ValidationReport()
    seen_ids: set[str] = set()
    for belief in beliefs:
        if belief.belief_id in seen_ids:
            report.add("error", "Duplicate belief_id detected.", belief.belief_id)
        seen_ids.add(belief.belief_id)

        if not belief.claim.strip():
            report.add("error", "Belief claim is empty.", belief.belief_id)
        if not belief.scope.repository_id.strip():
            report.add("error", "Belief scope.repository_id is empty.", belief.belief_id)
        if not (0.0 <= belief.confidence <= 1.0):
            report.add("error", "Belief confidence must be in [0, 1].", belief.belief_id)
        if not (0.0 <= belief.importance_score <= 1.0):
            report.add("error", "Belief importance_score must be in [0, 1].", belief.belief_id)
        if not belief.evidence:
            report.add("warning", "Belief has no supporting evidence.", belief.belief_id)
        if not belief.scope.file_paths and not belief.scope.symbols and not belief.scope.related_tests:
            report.add("warning", "Belief has empty operational scope.", belief.belief_id)
    return report


def validate_events(events: list[ChangeEvent]) -> ValidationReport:
    report = ValidationReport()
    seen_ids: set[str] = set()
    for event in events:
        if event.event_id in seen_ids:
            report.add("error", "Duplicate event_id detected.", event.event_id)
        seen_ids.add(event.event_id)

        if not event.summary.strip():
            report.add("error", "Event summary is empty.", event.event_id)
        if not event.paths and not event.symbols:
            report.add("warning", "Event has neither paths nor symbols.", event.event_id)
    return report


def render_validation_report(report: ValidationReport, title: str) -> str:
    lines = [title, f"valid={report.is_valid}", f"issues={len(report.issues)}"]
    for issue in report.issues:
        object_part = f" [{issue.object_id}]" if issue.object_id else ""
        lines.append(f"- {issue.level}{object_part}: {issue.message}")
    return "\n".join(lines)
