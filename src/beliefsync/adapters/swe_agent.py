from __future__ import annotations

from .base import AgentAdapter


class SWEAgentAdapter(AgentAdapter):
    """
    Placeholder adapter for future SWE-agent integration.

    The intended contract is:
    - map trajectory state to beliefs
    - convert repository updates to ChangeEvents
    - surface stale-belief findings back to the agent controller
    """

    def export_beliefs(self):
        raise NotImplementedError("SWE-agent integration is not implemented yet.")

    def export_events(self):
        raise NotImplementedError("SWE-agent integration is not implemented yet.")

    def ingest_revalidation_summary(self, summary: str) -> None:
        raise NotImplementedError("SWE-agent integration is not implemented yet.")
