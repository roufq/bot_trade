import sys
from pathlib import Path
import unittest

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import ai_trader


class TrainingPreparationTests(unittest.TestCase):
    def test_entry_sl_tp_survive_merge_suffixes(self):
        entry = {column: 0.0 for column in [
            "h1_ema_gap", "h1_rsi", "h1_atr", "m15_ema_gap", "m15_rsi",
            "m15_atr", "trend_strength", "close_to_ema_fast", "ema_gap_ratio",
            "price_vs_ema_fast", "rsi_diff_m15", "h1_ema_slope",
            "m15_ema_slope", "atr_ratio", "spread_points",
        ]}
        entry.update({
            "timestamp": "2026-07-21T10:00:00", "order_id": "1",
            "position_ticket": "10", "signal": "buy", "entry_time": "2026-07-21T10:00:00",
            "entry_price": 100.0, "sl_price": 99.0, "tp_price": 102.0,
        })
        closed = {
            "timestamp": "2026-07-21T10:05:00", "order_id": "1", "ticket": "10",
            "signal": "buy", "sl_price": 99.0, "tp_price": 102.0, "profit": 2.0,
        }
        prepared = ai_trader._prepare_dataframe_from_trade_log(
            pd.DataFrame([entry]), pd.DataFrame([closed])
        )
        self.assertEqual(len(prepared), 1)
        self.assertEqual(prepared.iloc[0]["sl_distance"], 1.0)
        self.assertEqual(prepared.iloc[0]["tp_distance"], 2.0)


if __name__ == "__main__":
    unittest.main()
