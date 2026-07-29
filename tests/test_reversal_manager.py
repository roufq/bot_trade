import sys
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config
import reversal_manager


def position(ticket=10, position_type=1, opened=100.0, sl=101.2, timestamp=900.0):
    return SimpleNamespace(
        ticket=ticket, type=position_type, price_open=opened, sl=sl,
        time=timestamp, magic=config.MT5_MAGIC,
    )


def signal(confluence=2):
    return SimpleNamespace(confluence_count=confluence)


class ControlledReversalTests(unittest.TestCase):
    def settings(self):
        return patch.multiple(
            config,
            CONTROLLED_REVERSAL_ENABLED=True,
            REVERSAL_MIN_CONFLUENCE=2,
            REVERSAL_MIN_ENTRY_SCORE=0.65,
            REVERSAL_SCORE_EDGE=0.10,
            REVERSAL_MIN_POSITION_AGE_SECONDS=60,
            REVERSAL_MAX_ADVERSE_R=0.75,
        )

    def test_single_signal_is_held(self):
        with self.settings():
            result = reversal_manager.decide(
                signal_result=signal(1), combined_score=0.9,
                opposite_positions=[position()], foreign_opposite_positions=[],
                entry_scores={10: 0.5}, current_price=100.2, now=1000.0,
            )
        self.assertEqual(result.action, "hold")
        self.assertIn("konfirmasi", result.reason)

    def test_foreign_position_is_never_reversed(self):
        with self.settings():
            result = reversal_manager.decide(
                signal_result=signal(), combined_score=0.9,
                opposite_positions=[position()], foreign_opposite_positions=[position(11)],
                entry_scores={10: 0.5}, current_price=100.2, now=1000.0,
            )
        self.assertEqual(result.action, "hold")
        self.assertIn("manual/EA lain", result.reason)

    def test_weak_score_edge_is_held(self):
        with self.settings():
            result = reversal_manager.decide(
                signal_result=signal(), combined_score=0.69,
                opposite_positions=[position()], foreign_opposite_positions=[],
                entry_scores={10: 0.65}, current_price=100.2, now=1000.0,
            )
        self.assertEqual(result.action, "hold")
        self.assertIn("tesis lama", result.reason)

    def test_strong_confirmed_signal_closes_and_reverses(self):
        with self.settings():
            result = reversal_manager.decide(
                signal_result=signal(3), combined_score=0.85,
                opposite_positions=[position()], foreign_opposite_positions=[],
                entry_scores={10: 0.60}, current_price=100.2, now=1000.0,
            )
        self.assertEqual(result.action, "close_and_reverse")

    def test_late_reversal_near_stop_is_held(self):
        with self.settings():
            result = reversal_manager.decide(
                signal_result=signal(3), combined_score=0.95,
                opposite_positions=[position()], foreign_opposite_positions=[],
                entry_scores={10: 0.5}, current_price=101.0, now=1000.0,
            )
        self.assertEqual(result.action, "hold")
        self.assertIn("terlambat", result.reason)


if __name__ == "__main__":
    unittest.main()
