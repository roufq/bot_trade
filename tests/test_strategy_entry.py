import sys
from pathlib import Path
import unittest
from unittest.mock import patch

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import strategy


class MomentumDistanceTests(unittest.TestCase):
    def _frame(self, last_close: float) -> pd.DataFrame:
        fast = f"ema_{strategy.config.EMA_ENTRY_FAST}"
        slow = f"ema_{strategy.config.EMA_ENTRY_SLOW}"
        return pd.DataFrame([
            {"close": 100.6, "atr": 1.0, "rsi": 40.0, fast: 100.0, slow: 100.8},
            {"close": last_close, "atr": 1.0, "rsi": 40.0, fast: 100.0, slow: 101.0},
        ])

    def test_momentum_can_enter_within_relaxed_atr_distance(self):
        frame = self._frame(99.5)
        with patch.object(strategy, "add_all_indicators", return_value=frame), \
                patch.object(strategy.config, "ALLOW_TREND_CONTINUATION_ENTRIES", False), \
                patch.object(strategy.config, "ENTRY_CLOSE_TO_EMA_MAX_ATR_MULTIPLIER", 0.55):
            result = strategy.check_entry_signal(frame, "sell")
        self.assertEqual(result.signal, "sell")

    def test_momentum_still_rejects_chasing_price_too_far_from_ema(self):
        frame = self._frame(99.2)
        with patch.object(strategy, "add_all_indicators", return_value=frame), \
                patch.object(strategy.config, "ALLOW_TREND_CONTINUATION_ENTRIES", False), \
                patch.object(strategy.config, "ENTRY_CLOSE_TO_EMA_MAX_ATR_MULTIPLIER", 0.55):
            result = strategy.check_entry_signal(frame, "sell")
        self.assertEqual(result.signal, "none")
