import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config
import stop_review


class StopReviewTests(unittest.TestCase):
    def test_classifies_sell_stop_that_later_reaches_original_tp(self):
        with TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "review.csv")
            with patch.object(config, "STOP_REVIEW_LOG_FILE", path), patch.object(config, "STOP_REVIEW_HORIZON_BARS", 5):
                stop_review.record(1, "sell", "2026-01-01 10:00:00", 100, 101, 98.5)
                candles = pd.DataFrame({
                    "time": pd.date_range("2026-01-01 10:01:00", periods=5, freq="min"),
                    "high": [101.1, 100.5, 100.2, 100.0, 99.0],
                    "low": [100.0, 99.5, 99.0, 98.4, 98.0],
                })
                self.assertEqual(stop_review.resolve(candles), 1)
                self.assertEqual(stop_review._read()[0]["classification"], "wick_stop_tp_recovered")

    def test_waits_for_complete_review_horizon(self):
        with TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "review.csv")
            with patch.object(config, "STOP_REVIEW_LOG_FILE", path), patch.object(config, "STOP_REVIEW_HORIZON_BARS", 5):
                stop_review.record(1, "buy", "2026-01-01 10:00:00", 100, 99, 102)
                candles = pd.DataFrame({
                    "time": pd.date_range("2026-01-01 10:01:00", periods=4, freq="min"),
                    "high": [100] * 4, "low": [99] * 4,
                })
                self.assertEqual(stop_review.resolve(candles), 0)


if __name__ == "__main__":
    unittest.main()
