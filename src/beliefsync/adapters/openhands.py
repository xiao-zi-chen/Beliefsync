from __future__ import annotations

from .base import AgentAdapter


class OpenHandsAdapter(AgentAdapter):
    """
    Placeholder adapter for future OpenHands integration.

    The intended contract is:
    - collect agent hypotheses and task context
    - export them as BeliefSync beliefs
    - collect repository change notifications
    - feed revalidation summaries back into the agent loop
    """

    def export_beliefs(self):
        raise NotImplementedError("OpenHands integration is not implemented yet.")

    def export_events(self):
        raise NotImplementedError("OpenHands integration is not implemented yet.")

    def ingest_revalidation_summary(self, summary: str) -> None:
        raise NotImplementedError("OpenHands integration is not implemented yet.")
