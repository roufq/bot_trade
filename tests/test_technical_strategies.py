import sys
from pathlib import Path
import unittest
from unittest.mock import patch

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import strategy
import technical_strategies as technical


def frame(rows: int = 40) -> pd.DataFrame:
    data = []
    for index in range(rows):
        center = 100.0 + ((index % 6) - 3) * 0.2
        data.append({
            "time": pd.Timestamp("2026-01-01 07:00") + pd.Timedelta(minutes=index),
            "open": center - 0.05,
            "high": center + 0.3,
            "low": center - 0.3,
            "close": center + 0.05,
            "volume": 100 + index,
        })
    return pd.DataFrame(data)


class IndependentDetectorTests(unittest.TestCase):
    def test_registry_exposes_every_strategy_separately(self):
        results = technical.evaluate_all(frame(60), frame(60))
        self.assertEqual([item.code for item in results], list("CDEFGHIJKL"))
        self.assertEqual(len({item.name for item in results}), 10)

    def test_liquidity_sweep_is_independent_buy_signal(self):
        data = frame()
        data.loc[30, ["open", "high", "low", "close"]] = [99.4, 99.7, 98.8, 99.5]
        data.loc[31:38, "low"] = 99.2
        data.loc[39, ["open", "high", "low", "close"]] = [99.2, 100.0, 98.5, 99.6]
        result = technical.liquidity(data)
        self.assertEqual((result.code, result.direction), ("D", "buy"))
        self.assertTrue(result.primary)

    def test_displacement_and_volume_remain_distinct(self):
        data = frame()
        data.loc[39, ["open", "high", "low", "close", "volume"]] = [99.0, 101.4, 98.9, 101.2, 1000]
        displacement = technical.displacement(data)
        volume = technical.volume(data)
        self.assertEqual((displacement.code, displacement.direction), ("H", "buy"))
        self.assertEqual((volume.code, volume.direction), ("K", "buy"))


class TechnicalConfluenceTests(unittest.TestCase):
    def _signal(self, code: str, direction: str, score: float, primary: bool = False):
        return technical.TechnicalSignal(code, technical.TECHNIQUE_CODES[code], direction, score, "test", primary)

    def test_requires_primary_setup_and_two_confirmations(self):
        only_confirmations = [self._signal("H", "buy", .8), self._signal("K", "buy", .7)]
        with patch.object(strategy.config, "TECHNICAL_MIN_CONFIRMATIONS", 2):
            result = strategy.combine_technical_signals(only_confirmations, 1.0, 100.0)
        self.assertEqual(result.signal, "none")

        valid = [self._signal("D", "buy", .8, True), self._signal("H", "buy", .7)]
        with patch.object(strategy.config, "TECHNICAL_MIN_CONFIRMATIONS", 2):
            result = strategy.combine_technical_signals(valid, 1.0, 100.0)
        self.assertEqual((result.signal, result.strategy_source), ("buy", "D_PLUS_H"))

    def test_strong_opposition_vetoes_entry(self):
        signals = [
            self._signal("C", "buy", .8, True), self._signal("H", "buy", .7),
            self._signal("D", "sell", .8, True), self._signal("E", "sell", .7, True),
        ]
        result = strategy.combine_technical_signals(signals, 1.0, 100.0)
        self.assertEqual(result.signal, "none")

    def test_legacy_and_technical_conflict_is_cancelled(self):
        legacy = strategy.TradeSignal("buy", "legacy", strategy_source="A_ONLY")
        modular = strategy.TradeSignal("sell", "modular", strategy_source="D_PLUS_H")
        result = strategy.merge_legacy_and_technical(legacy, modular)
        self.assertEqual((result.signal, result.strategy_source), ("none", "CONFLICT"))

    def test_neutral_technical_payload_is_rebased_to_legacy_direction(self):
        legacy = strategy.TradeSignal("buy", "legacy", strategy_source="A_ONLY")
        modular = strategy.TradeSignal(
            "none", "insufficient", strategy_source="NONE",
            technique_scores={"C": -0.8, "D": -0.7, "L": 0.6},
            technique_signals={"C": "buy", "D": "sell", "L": "none"},
        )
        result = strategy.merge_legacy_and_technical(legacy, modular)
        self.assertEqual(result.technique_scores, {"C": 0.8, "D": -0.7, "L": 0.6})


if __name__ == "__main__":
    unittest.main()
