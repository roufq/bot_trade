import sys
from pathlib import Path
import unittest
from unittest.mock import patch
import tempfile

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import ai_trader
from strategy import TradeSignal


class _LegacyClassifier:
    def predict_proba(self, frame):
        assert list(frame.columns) == ai_trader.FEATURE_COLUMNS[:19]
        return [[0.4, 0.6]]


class TrainingPreparationTests(unittest.TestCase):
    def test_signal_side_is_known_entry_feature_not_target_leakage(self):
        self.assertIn("signal_side", ai_trader.FEATURE_COLUMNS)
        self.assertNotIn("target", ai_trader.FEATURE_COLUMNS)
        self.assertNotIn("r_multiple", ai_trader.FEATURE_COLUMNS)

    def test_predict_uses_feature_contract_saved_in_legacy_bundle(self):
        candles = pd.DataFrame([
            {"time": pd.Timestamp("2026-01-01") + pd.Timedelta(minutes=i),
             "open": 100 + i * .01, "high": 100.3 + i * .01,
             "low": 99.7 + i * .01, "close": 100.1 + i * .01}
            for i in range(60)
        ])
        bundle = {"classifier": _LegacyClassifier(), "features": ai_trader.FEATURE_COLUMNS[:19]}
        with patch.object(ai_trader, "_load_model", return_value=bundle):
            result = ai_trader.predict(candles, candles, TradeSignal("buy", "test", atr_value=1.0))
        self.assertAlmostEqual(result.win_probability, 0.6)

    def test_model_status_distinguishes_missing_and_corrupt_model(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ml_model.joblib"
            with patch.object(ai_trader.config, "MODEL_FILE", str(path)), \
                    patch.object(ai_trader.config, "AI_MODEL_REGISTRY_DIR", str(Path(directory) / "registry")):
                self.assertEqual(ai_trader.model_status()[0], False)
                self.assertIn("belum ada kandidat", ai_trader.model_status()[1])
                path.write_text("not a joblib model", encoding="utf-8")
                self.assertIsNone(ai_trader._load_model())
                available, reason = ai_trader.model_status()
                self.assertFalse(available)
                self.assertIn("gagal dimuat", reason)

    def test_shadow_training_requires_resolved_reject_and_complete_snapshot(self):
        features = {name: 0.1 for name in ai_trader.FEATURE_COLUMNS}
        shadow = pd.DataFrame([{
            "signal_time": "2026-01-01 10:00:00", "signal": "buy",
            "strategy_source": "C_PLUS_D", "decision": "ai_reject",
            "status": "resolved", "result_r": 1.5,
            "features_json": __import__("json").dumps(features),
        }, {
            "signal_time": "2026-01-01 10:01:00", "signal": "sell",
            "decision": "ai_accept", "status": "resolved", "result_r": -1.0,
            "features_json": __import__("json").dumps(features),
        }])
        prepared = ai_trader._prepare_shadow_dataframe(shadow)
        self.assertEqual(len(prepared), 1)
        self.assertEqual(prepared.iloc[0]["sample_source"], "shadow")
        self.assertEqual(float(prepared.iloc[0]["r_multiple"]), 1.5)

    def test_training_loader_deduplicates_same_minute_and_direction(self):
        with tempfile.TemporaryDirectory() as directory:
            historical_path = Path(directory) / "historical.csv"
            rows = []
            for timestamp in ["2026-01-01T10:00:01", "2026-01-01 10:00:45"]:
                rows.append({
                    "signal_time": timestamp, "signal": "buy", "result_r": 1.5,
                    **{name: 0.1 for name in ai_trader.FEATURE_COLUMNS},
                })
            pd.DataFrame(rows).to_csv(historical_path, index=False)
            missing = str(Path(directory) / "missing.csv")
            with patch.object(ai_trader.config, "TRADE_LOG_FILE", missing), \
                    patch.object(ai_trader.config, "CLOSED_TRADE_LOG_FILE", missing), \
                    patch.object(ai_trader.config, "SHADOW_SIGNAL_LOG_FILE", missing), \
                    patch.object(ai_trader.config, "HISTORICAL_SIGNAL_DATASET_FILE", str(historical_path)):
                samples = ai_trader.load_training_samples()
        self.assertEqual(len(samples), 1)

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
            "risk_amount": 1.0,
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
        self.assertEqual(prepared.iloc[0]["r_multiple"], 2.0)


if __name__ == "__main__":
    unittest.main()
