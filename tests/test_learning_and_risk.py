import sys
from pathlib import Path
from types import SimpleNamespace
import unittest

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import learner
import risk_manager


class LearningQualityTests(unittest.TestCase):
    def test_segment_is_setup_only_not_trade_direction(self):
        from types import SimpleNamespace
        from unittest.mock import patch
        history = pd.DataFrame({
            "profit": [1, -1, 2, -1, 1, 1], "risk_amount": [1] * 6,
            "entry_signal": ["buy", "sell", "buy", "sell", "buy", "sell"],
            "entry_reason": ["Momentum entry"] * 6,
        })
        with patch.object(learner, "_load_enriched_history", return_value=history), \
             patch.object(learner, "estimate_market_score", return_value=.5):
            decision = learner.decide(
                pd.DataFrame(), pd.DataFrame(), 0,
                SimpleNamespace(signal="sell", reason="Momentum entry"),
            )
        self.assertEqual(decision.segment, "momentum")
        self.assertEqual(decision.segment_trades, 6)

    def test_metrics_distinguish_profit_size_using_r_multiple(self):
        df = pd.DataFrame({"profit": [0.1, 2.0, -1.0], "risk_amount": [1.0, 1.0, 1.0]})
        metrics = learner.calculate_trade_metrics(df)
        self.assertAlmostEqual(metrics["average_r"], 1.1 / 3.0)
        self.assertAlmostEqual(metrics["profit_factor"], 2.1)

    def test_rejects_uniform_corrupt_history(self):
        df = pd.DataFrame({
            "timestamp": pd.date_range("2026-07-01", periods=60, freq="h").astype(str),
            "ticket": [str(i // 2) for i in range(60)],
            "profit": [5.41] * 60,
        })
        valid, reason = learner.validate_closed_trade_history(df)
        self.assertFalse(valid)
        self.assertTrue("duplikat" in reason or "variasi" in reason)

    def test_accepts_varied_unique_history(self):
        profits = [2.0, -1.0, 3.5, -2.0, 0.5] * 10
        df = pd.DataFrame({
            "timestamp": pd.date_range("2026-07-01", periods=50, freq="h").astype(str),
            "ticket": [str(i) for i in range(50)],
            "profit": profits,
        })
        self.assertTrue(learner.validate_closed_trade_history(df)[0])


class RiskSizingTests(unittest.TestCase):
    def test_structural_sell_stop_uses_confirmed_swing_and_spread_buffer(self):
        highs = [99, 100, 101, 105, 102, 101, 100, 101, 100]
        frame = pd.DataFrame({
            "time": pd.date_range("2026-01-01", periods=len(highs), freq="min"),
            "high": highs, "low": [value - 2 for value in highs],
        })
        stop, reason = risk_manager.structural_stop_price(
            frame, "sell", entry_price=103.0, atr_value=1.0,
            spread_price=0.2, tick_size=0.01,
        )
        self.assertEqual(stop, 105.3)
        self.assertIn("buffer=0.30000", reason)

    def test_plan_rejects_structural_stop_that_makes_reward_risk_too_low(self):
        plan = risk_manager.build_order_plan(
            signal="buy", entry_price=100, atr_value=1, equity=1000,
            contract_size=100, tick_value=1, tick_size=0.01,
            volume_min=0.01, volume_max=100, volume_step=0.01,
            risk_percent=0.5, structural_sl_price=98.5,
        )
        self.assertIsNone(plan)

    def test_structural_stop_reduces_lot_to_preserve_cash_risk(self):
        plan = risk_manager.build_order_plan(
            signal="buy", entry_price=100, atr_value=2, equity=10000,
            contract_size=100, tick_value=1, tick_size=0.01,
            volume_min=0.01, volume_max=100, volume_step=0.01,
            risk_percent=0.5, structural_sl_price=97.5,
        )
        self.assertIsNotNone(plan)
        self.assertLessEqual(plan.risk_amount, 50.0)

    def test_rejects_minimum_lot_when_it_exceeds_risk_budget(self):
        plan = risk_manager.build_order_plan(
            signal="buy", entry_price=4000, atr_value=2, equity=100,
            contract_size=100, tick_value=1, tick_size=0.01,
            volume_min=0.01, volume_max=100, volume_step=0.01,
            risk_percent=0.5,
        )
        self.assertIsNone(plan)

    def test_allows_minimum_lot_within_hard_risk_limit(self):
        plan = risk_manager.build_order_plan(
            signal="buy", entry_price=4000, atr_value=2, equity=300,
            contract_size=100, tick_value=1, tick_size=0.01,
            volume_min=0.01, volume_max=100, volume_step=0.01,
            risk_percent=0.5,
        )
        self.assertIsNotNone(plan)
        self.assertEqual(plan.lot_size, 0.01)
        self.assertAlmostEqual(plan.risk_amount, 2 * risk_manager.config.SL_ATR_MULTIPLIER)

    def test_open_risk_uses_stop_distance(self):
        positions = [SimpleNamespace(price_open=100.0, sl=99.0, volume=0.1)]
        risk = risk_manager.calculate_total_open_risk_percent(positions, 1000, 1, 0.1)
        self.assertAlmostEqual(risk, 0.1)


if __name__ == "__main__":
    unittest.main()
