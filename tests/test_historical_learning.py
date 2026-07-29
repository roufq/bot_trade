import sys
from pathlib import Path
import unittest

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import historical_learning


class HistoricalOutcomeTests(unittest.TestCase):
    def test_same_candle_sl_and_tp_is_conservative_loss(self):
        future = pd.DataFrame([{
            "time": "2026-01-01 00:01:00", "high": 102.0, "low": 98.0,
        }])
        result = historical_learning._outcome(future, "buy", 100.0, 1.0)
        self.assertEqual(result[0], -1.0)

    def test_take_profit_returns_configured_r_multiple(self):
        future = pd.DataFrame([{
            "time": "2026-01-01 00:01:00", "high": 102.0, "low": 99.5,
        }])
        result = historical_learning._outcome(future, "buy", 100.0, 1.0)
        self.assertGreater(result[0], 0.0)


if __name__ == "__main__":
    unittest.main()
