import sys
from pathlib import Path
from types import SimpleNamespace
import unittest

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import learner
import risk_manager


class LearningQualityTests(unittest.TestCase):
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
        self.assertAlmostEqual(plan.risk_amount, 2.4)

    def test_open_risk_uses_stop_distance(self):
        positions = [SimpleNamespace(price_open=100.0, sl=99.0, volume=0.1)]
        risk = risk_manager.calculate_total_open_risk_percent(positions, 1000, 1, 0.1)
        self.assertAlmostEqual(risk, 0.1)


if __name__ == "__main__":
    unittest.main()
