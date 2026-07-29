from datetime import datetime
from types import SimpleNamespace
import sys
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import execution_guard
import config
import performance_guard
import risk_manager
import runtime_guard
import news_filter


class ExposureTests(unittest.TestCase):
    def test_rejects_opposite_position_when_hedging_disabled(self):
        existing = SimpleNamespace(type=1, profit=1.0, price_open=100.0)
        with patch.object(config, "ALLOW_OPPOSITE_HEDGE", False):
            allowed, reason = risk_manager.can_open_direction([existing], "buy", 101.0, 1.0)
        self.assertFalse(allowed)
        self.assertIn("berlawanan", reason)

    def test_rejects_averaging_into_losing_position(self):
        pos = SimpleNamespace(type=0, price_open=100.0, profit=-1.0)
        allowed, reason = risk_manager.can_open_direction([pos], "buy", 101.0, 1.0)
        self.assertFalse(allowed)
        self.assertIn("floating loss", reason)


class ExecutionGuardTests(unittest.TestCase):
    def test_rejects_insufficient_remaining_margin(self):
        with patch.object(execution_guard.mt5_connector, "get_tick_info", return_value={"time": 1000}), patch.object(
            execution_guard.time, "time", return_value=1001
        ), patch.object(execution_guard.mt5_connector, "calculate_order_margin", return_value=60.0):
            allowed, reason = execution_guard.validate_market_order(
                "X", "buy", 0.01, 100, 99, 102,
                {"point": .01, "trade_tick_size": .01, "trade_stops_level": 10, "volume_min": .01, "volume_max": 10},
                {"margin_free": 100},
            )
        self.assertFalse(allowed)
        self.assertIn("margin", reason)


class PerformanceGuardTests(unittest.TestCase):
    def test_stops_negative_rolling_expectancy(self):
        df = pd.DataFrame({
            "profit": [-1.0] * 10, "risk_amount": [1.0] * 10,
            "exit_time": ["2026-07-23T10:00:00"] * 10,
        })
        allowed, reason, _ = performance_guard.evaluate(df, datetime(2026, 7, 23, 10, 5))
        self.assertFalse(allowed)
        self.assertIn("rolling melemah", reason)

    def test_negative_rolling_enters_probe_mode_after_pause(self):
        df = pd.DataFrame({
            "profit": [-1.0] * 10, "risk_amount": [1.0] * 10,
            "exit_time": ["2026-07-23T10:00:00"] * 10,
        })
        allowed, reason, metrics = performance_guard.evaluate(df, datetime(2026, 7, 23, 10, 11))
        self.assertTrue(allowed)
        self.assertIn("mode probe", reason)
        self.assertTrue(metrics["probe_mode"])

    def test_oversized_loss_only_blocks_for_cooldown(self):
        from datetime import datetime
        rows = pd.DataFrame({
            "timestamp": ["2026-07-22T09:00:00"] * 10,
            "exit_time": ["2026-07-22T09:00:00"] * 10,
            "profit": [2.0] * 9 + [-2.0],
            "risk_amount": [1.0] * 10,
        })
        blocked, _, _ = performance_guard.evaluate(rows, datetime(2026, 7, 22, 9, 5))
        allowed, _, metrics = performance_guard.evaluate(rows, datetime(2026, 7, 22, 10, 0))
        self.assertFalse(blocked)
        self.assertTrue(allowed)
        self.assertTrue(metrics["oversized_loss_cooldown_complete"])


class OrderCircuitTests(unittest.TestCase):
    def test_three_errors_open_circuit(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = str(Path(tmpdir) / "state.json")
            now = datetime(2026, 7, 21, 10, 0)
            with patch.object(runtime_guard.config, "RUNTIME_STATE_FILE", state_path):
                for _ in range(3):
                    runtime_guard.record_order_result(False, now)
                self.assertFalse(runtime_guard.order_circuit_status(now)[0])


class NewsFilterTests(unittest.TestCase):
    def test_high_impact_usd_event_blocks_entry(self):
        events = [{"time": "2026-07-21T10:00:00+07:00", "currency": "USD", "impact": "high", "title": "CPI"}]
        blocked, reason = news_filter.event_blackout(events, datetime(2026, 7, 21, 9, 50))
        self.assertTrue(blocked)
        self.assertIn("CPI", reason)

    def test_fmp_country_and_event_fields_are_supported(self):
        events = [{"date": "2026-07-21T03:00:00Z", "country": "US", "impact": "High", "event": "NFP"}]
        local_event = news_filter._parse_time("2026-07-21T03:00:00Z")
        blocked, reason = news_filter.event_blackout(events, local_event)
        self.assertTrue(blocked)
        self.assertIn("NFP", reason)

    def test_failed_calendar_request_is_throttled(self):
        news_filter._cache.update({"loaded_at": 0.0, "events": []})
        with patch.object(news_filter.config, "NEWS_CALENDAR_URL", "https://invalid.test"), \
                patch.object(news_filter.config, "NEWS_REFRESH_SECONDS", 300), \
                patch.object(news_filter.time, "time", side_effect=[1000.0, 1000.0, 1001.0]), \
                patch.object(news_filter.requests, "get", side_effect=requests.RequestException) as request:
            self.assertIn("gagal", news_filter.is_blackout()[1])
            self.assertEqual(news_filter.is_blackout(), (False, ""))
        self.assertEqual(request.call_count, 1)


if __name__ == "__main__":
    unittest.main()
