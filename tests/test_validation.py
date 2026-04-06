import unittest

from beliefsync.models import Belief, BeliefType, Scope
from beliefsync.validation import validate_beliefs, validate_events
from beliefsync.models import ChangeEvent, EventType


class ValidationTests(unittest.TestCase):
    def test_validate_beliefs_flags_empty_claim(self):
        beliefs = [
            Belief(
                belief_id="b1",
                belief_type=BeliefType.BUG_LOCALIZATION,
                claim="",
                scope=Scope(repository_id="demo/repo"),
            )
        ]
        report = validate_beliefs(beliefs)
        self.assertFalse(report.is_valid)

    def test_validate_events_flags_empty_summary(self):
        events = [
            ChangeEvent(
                event_id="e1",
                event_type=EventType.CODE_DIFF,
                summary="",
                paths=["src/main.py"],
            )
        ]
        report = validate_events(events)
        self.assertFalse(report.is_valid)


if __name__ == "__main__":
    unittest.main()
