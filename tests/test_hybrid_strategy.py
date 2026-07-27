import sys
from pathlib import Path
import unittest

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import strategy


def signal(direction: str, reason: str = "test") -> strategy.TradeSignal:
    return strategy.TradeSignal(direction, reason, atr_value=1.0, entry_price=100.0)


class HybridDecisionTests(unittest.TestCase):
    def test_a_only_is_allowed(self):
        result = strategy.combine_signals(signal("buy"), signal("none"))
        self.assertEqual((result.signal, result.strategy_source), ("buy", "A_ONLY"))

    def test_b_only_is_allowed(self):
        result = strategy.combine_signals(signal("none"), signal("sell"))
        self.assertEqual((result.signal, result.strategy_source), ("sell", "B_ONLY"))

    def test_same_direction_builds_confluence(self):
        result = strategy.combine_signals(signal("buy"), signal("buy"))
        self.assertEqual((result.signal, result.strategy_source), ("buy", "A_PLUS_B"))

    def test_opposite_directions_cancel_entry(self):
        result = strategy.combine_signals(signal("buy"), signal("sell"))
        self.assertEqual((result.signal, result.strategy_source), ("none", "CONFLICT"))

    def test_solo_risk_is_reduced_but_confluence_is_not_doubled(self):
        self.assertLess(strategy.risk_multiplier_for("A_ONLY"), 1.0)
        self.assertLess(strategy.risk_multiplier_for("B_ONLY"), 1.0)
        self.assertEqual(strategy.risk_multiplier_for("A_PLUS_B"), 1.0)


class FVGTests(unittest.TestCase):
    def _higher_timeframe(self) -> pd.DataFrame:
        rows = []
        for index in range(17):
            base = 100.0
            rows.append({
                "time": pd.Timestamp("2026-01-01") + pd.Timedelta(hours=index),
                "open": base, "high": base + 0.4, "low": base - 0.4, "close": base + 0.1,
            })
        rows[-3].update(open=99.8, high=100.0, low=99.5, close=99.9)
        rows[-2].update(open=100.2, high=101.4, low=100.1, close=101.2)
        rows[-1].update(open=101.6, high=102.0, low=101.5, close=101.8)
        return pd.DataFrame(rows)

    def test_detects_unfilled_bullish_fvg(self):
        zones = strategy.detect_fvg_zones(self._higher_timeframe(), "H1", 24)
        bullish = [zone for zone in zones if zone.direction == "buy"]
        self.assertTrue(bullish)
        self.assertAlmostEqual(bullish[-1].lower, 100.0)
        self.assertAlmostEqual(bullish[-1].upper, 101.5)

    def test_m1_rejection_triggers_fvg_signal(self):
        h1 = self._higher_timeframe()
        m15 = self._higher_timeframe()
        m1 = self._higher_timeframe()
        m1.loc[m1.index[-1], ["open", "high", "low", "close"]] = [100.4, 101.7, 100.2, 101.4]
        result = strategy.evaluate_fvg(h1, m15, m1)
        self.assertEqual(result.signal, "buy")
        self.assertEqual(result.strategy_source, "B_ONLY")

    def test_fully_filled_fvg_is_not_active(self):
        frame = self._higher_timeframe()
        extra = frame.iloc[-1].copy()
        extra["time"] = frame.iloc[-1]["time"] + pd.Timedelta(hours=1)
        extra[["open", "high", "low", "close"]] = [101.0, 101.2, 99.8, 100.1]
        frame = pd.concat([frame, pd.DataFrame([extra])], ignore_index=True)
        zones = strategy.detect_fvg_zones(frame, "H1", 24)
        self.assertFalse(any(zone.lower == 100.0 and zone.upper == 101.5 for zone in zones))


if __name__ == "__main__":
    unittest.main()
