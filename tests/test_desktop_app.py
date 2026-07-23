import sys
from pathlib import Path
import re
import unittest
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import desktop_app


class DesktopSettingsTests(unittest.TestCase):
    def test_installed_exe_uses_local_app_data(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            selected = desktop_app.choose_runtime_root(
                root / "Program", root / "Source", True,
                local_app_data=str(root / "Local"),
            )
            self.assertEqual(selected, root / "Local" / "AITradingDesktop" / "Data")

    def test_project_exe_keeps_existing_history(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "trade_log.csv").touch()
            selected = desktop_app.choose_runtime_root(
                root, root / "Source", True, local_app_data=str(root / "Local")
            )
            self.assertEqual(selected, root)

    def test_valid_settings(self):
        values = {
            "TRADING_SYMBOL": "XAUUSD.vx",
            "TRADING_RISK_PERCENT": "0.5",
            "TRADING_MAX_DAILY_DRAWDOWN_PERCENT": "5",
            "TRADING_MAX_SPREAD_POINTS": "50",
            "TRADING_MAX_SPREAD_ATR_RATIO": "0.35",
            "TRADING_MAX_OPEN_POSITIONS": "3",
            "TRADING_MAX_POSITIONS_PER_DIRECTION": "2",
            "TRADING_MT5_LOGIN": "12345",
        }
        self.assertEqual(desktop_app.validate_settings(values), [])

    def test_rejects_unsafe_or_invalid_numeric_values(self):
        values = {
            "TRADING_SYMBOL": "",
            "TRADING_RISK_PERCENT": "20",
            "TRADING_MAX_DAILY_DRAWDOWN_PERCENT": "abc",
            "TRADING_MAX_SPREAD_POINTS": "0",
            "TRADING_MAX_SPREAD_ATR_RATIO": "2",
            "TRADING_MAX_OPEN_POSITIONS": "2.5",
            "TRADING_MAX_POSITIONS_PER_DIRECTION": "11",
            "TRADING_MT5_LOGIN": "account",
        }
        self.assertGreaterEqual(len(desktop_app.validate_settings(values)), 8)

    def test_direction_limit_cannot_exceed_total_limit(self):
        values = {
            "TRADING_SYMBOL": "XAUUSD.vx",
            "TRADING_RISK_PERCENT": "0.5",
            "TRADING_MAX_DAILY_DRAWDOWN_PERCENT": "5",
            "TRADING_MAX_SPREAD_POINTS": "50",
            "TRADING_MAX_SPREAD_ATR_RATIO": "0.35",
            "TRADING_MAX_OPEN_POSITIONS": "2",
            "TRADING_MAX_POSITIONS_PER_DIRECTION": "3",
            "TRADING_MT5_LOGIN": "",
        }
        errors = desktop_app.validate_settings(values)
        self.assertTrue(any("satu arah" in error for error in errors))

    def test_rejects_inverted_indicator_and_schedule_ranges(self):
        values = {
            "TRADING_EMA_TREND_FAST": "60",
            "TRADING_EMA_TREND_SLOW": "20",
            "TRADING_RSI_BUY_MIN": "80",
            "TRADING_RSI_BUY_MAX": "60",
            "TRADING_HOUR_START": "20",
            "TRADING_HOUR_END": "8",
        }
        errors = desktop_app.validate_settings(values)
        self.assertTrue(any("EMA tren" in error for error in errors))
        self.assertTrue(any("RSI BUY" in error for error in errors))
        self.assertTrue(any("Jam trading" in error for error in errors))

    def test_every_preset_is_valid(self):
        for name, preset in desktop_app.TRADING_PRESETS.items():
            with self.subTest(name=name):
                self.assertEqual(desktop_app.validate_settings(preset), [])

    def test_news_calendar_url_must_be_http(self):
        errors = desktop_app.validate_settings({"TRADING_NEWS_CALENDAR_URL": "calendar.local"})
        self.assertTrue(any("URL kalender" in error for error in errors))

    def test_every_desktop_setting_is_consumed_by_config(self):
        config_source = (Path(__file__).resolve().parents[1] / "config.py").read_text(encoding="utf-8")
        referenced = set(re.findall(r'"(TRADING_[A-Z0-9_]+)"', config_source))
        desktop_fields = {item[1] for item in desktop_app.SETTING_FIELDS}
        self.assertEqual(desktop_fields - referenced, set())
        self.assertEqual(referenced - desktop_fields, set())

    def test_source_connection_tools_dispatch_through_desktop_cli(self):
        for mode in ("mt5", "telegram"):
            command = desktop_app.process_command(mode)
            self.assertEqual(command[-2:], ["--tool", mode])


if __name__ == "__main__":
    unittest.main()
