from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import Belief, ChangeEvent


class AgentAdapter(ABC):
    """Abstract integration point for coding-agent frameworks."""

    @abstractmethod
    def export_beliefs(self) -> list[Belief]:
        raise NotImplementedError

    @abstractmethod
    def export_events(self) -> list[ChangeEvent]:
        raise NotImplementedError

    @abstractmethod
    def ingest_revalidation_summary(self, summary: str) -> None:
        raise NotImplementedError
