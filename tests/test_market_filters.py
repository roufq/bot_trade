from datetime import datetime
import sys
from pathlib import Path
import unittest
from unittest.mock import patch

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import market_filters


class MarketFilterTests(unittest.TestCase):
    def test_second_loss_uses_progressive_cooldown(self):
        rows = pd.DataFrame({
            "timestamp": ["2026-07-21T10:00:00", "2026-07-21T10:01:00"],
            "exit_time": ["2026-07-21T10:00:00", "2026-07-21T10:01:00"],
            "profit": [-1.0, -1.0],
        })
        with patch.object(market_filters.config, "SECOND_CONSECUTIVE_LOSS_COOLDOWN_SECONDS", 180):
            blocked, reason = market_filters.recent_trade_guard(rows, datetime(2026, 7, 21, 10, 2))
            allowed, _ = market_filters.recent_trade_guard(rows, datetime(2026, 7, 21, 10, 4, 1))
        self.assertFalse(blocked)
        self.assertIn("loss streak 2", reason)
        self.assertTrue(allowed)

    def test_spread_guard(self):
        with patch.object(market_filters.config, "MAX_SPREAD_POINTS", 30), patch.object(
            market_filters.config, "MAX_SPREAD_ATR_RATIO", 0.2
        ):
            self.assertTrue(market_filters.check_spread(100.20, 100.00, 0.01, 2.0)[0])
            self.assertFalse(market_filters.check_spread(100.50, 100.00, 0.01, 2.0)[0])

    def test_spread_between_twenty_and_twenty_five_percent_is_allowed(self):
        with patch.object(market_filters.config, "MAX_SPREAD_ATR_RATIO", 0.25):
            self.assertTrue(market_filters.check_spread(100.23, 100.00, 0.01, 1.0)[0])

    def test_spread_below_thirty_five_percent_is_available_for_quiet_market_mode(self):
        with patch.object(market_filters.config, "MAX_SPREAD_ATR_RATIO", 0.35):
            self.assertTrue(market_filters.check_spread(100.32, 100.00, 0.01, 1.0)[0])
            self.assertFalse(market_filters.check_spread(100.36, 100.00, 0.01, 1.0)[0])

    def test_manual_news_blackout(self):
        with patch.object(market_filters.config, "NEWS_BLACKOUT_WINDOWS", ["13:25-13:40"]):
            self.assertTrue(market_filters.in_news_blackout(datetime(2026, 7, 21, 13, 30))[0])
            self.assertFalse(market_filters.in_news_blackout(datetime(2026, 7, 21, 13, 50))[0])

    def test_loss_cooldown(self):
        df = pd.DataFrame({"profit": [-2.0], "exit_time": ["2026-07-21 10:00:00"]})
        with patch.object(market_filters.config, "COOLDOWN_AFTER_LOSS_SECONDS", 180):
            self.assertFalse(market_filters.recent_trade_guard(df, datetime(2026, 7, 21, 10, 1))[0])
            self.assertTrue(market_filters.recent_trade_guard(df, datetime(2026, 7, 21, 10, 4))[0])

    def test_future_server_time_falls_back_to_local_log_time(self):
        df = pd.DataFrame({
            "profit": [2.0],
            "exit_time": ["2026-07-21 13:00:00"],
            "timestamp": ["2026-07-21 10:00:00"],
        })
        with patch.object(market_filters.config, "COOLDOWN_AFTER_WIN_SECONDS", 60):
            allowed, _ = market_filters.recent_trade_guard(df, datetime(2026, 7, 21, 10, 2))
        self.assertTrue(allowed)


if __name__ == "__main__":
    unittest.main()
