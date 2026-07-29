import sys
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import shadow_tracker


class ShadowTrackerTests(unittest.TestCase):
    def test_records_and_resolves_rejected_signal(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = str(Path(tmpdir) / "shadow.csv")
            with patch.object(shadow_tracker.config, "SHADOW_SIGNAL_LOG_FILE", path):
                shadow_tracker.record(
                    "2026-07-22 10:00:00", "buy", "momentum", 100, 1, .4, -.2, .1,
                    "ai_reject", strategy_source="C_PLUS_D",
                    feature_values={"liquidity_score": 0.8},
                )
                candles = pd.DataFrame([
                    {"time": "2026-07-22 10:01:00", "high": 100.5, "low": 98.7},
                ])
                self.assertEqual(shadow_tracker.resolve(candles), 1)
                row = shadow_tracker._read()[0]
                self.assertEqual(row["decision"], "ai_reject")
                self.assertEqual(float(row["result_r"]), -1.0)
                self.assertEqual(row["strategy_source"], "C_PLUS_D")
                self.assertIn('"liquidity_score":0.8', row["features_json"])


if __name__ == "__main__":
    unittest.main()
