import sys
import tempfile
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import runtime_guard


class RuntimeGuardTests(unittest.TestCase):
    def test_first_run_initializes_account_bound_equity_baselines(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = str(Path(tmpdir) / "state.json")
            with patch.object(runtime_guard.config, "RUNTIME_STATE_FILE", path), \
                 patch.object(runtime_guard.config, "MT5_SERVER", "Demo-Server"):
                reset, reason = runtime_guard.ensure_account_state(
                    {"login": 12345, "equity": 300.0}, datetime(2026, 7, 29, 10)
                )
                state = runtime_guard.load_state()
            self.assertTrue(reset)
            self.assertIn("baseline equity", reason)
            self.assertEqual(state["equity_peak"], 300.0)
            self.assertEqual(state["day_start_equity"], 300.0)
            self.assertEqual(state["week_start_equity"], 300.0)
            self.assertEqual(state["account_key"], "demo-server|12345")

    def test_legacy_state_is_reset_once_then_preserved_for_same_account(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "state.json"
            path.write_text('{"equity_peak": 900.0, "day_start_equity": 900.0}', encoding="utf-8")
            account = {"login": 12345, "equity": 300.0, "company": "Broker Demo"}
            with patch.object(runtime_guard.config, "RUNTIME_STATE_FILE", str(path)), \
                 patch.object(runtime_guard.config, "MT5_SERVER", ""):
                first_reset, _ = runtime_guard.ensure_account_state(account, datetime(2026, 7, 29, 10))
                second_reset, _ = runtime_guard.ensure_account_state(account, datetime(2026, 7, 29, 11))
                _, _, peak_dd = runtime_guard.update_equity_state(270.0, datetime(2026, 7, 29, 11))
            self.assertTrue(first_reset)
            self.assertFalse(second_reset)
            self.assertAlmostEqual(peak_dd, 10.0)

    def test_switching_mt5_account_resets_foreign_peak_and_tickets(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = str(Path(tmpdir) / "state.json")
            with patch.object(runtime_guard.config, "RUNTIME_STATE_FILE", path), \
                 patch.object(runtime_guard.config, "MT5_SERVER", "Demo"):
                runtime_guard.ensure_account_state({"login": 111, "equity": 900.0})
                runtime_guard.save_tracked_tickets({77})
                reset, _ = runtime_guard.ensure_account_state({"login": 222, "equity": 300.0})
                state = runtime_guard.load_state()
            self.assertTrue(reset)
            self.assertEqual(state["equity_peak"], 300.0)
            self.assertEqual(state["open_tickets"], [])

    def test_single_instance_lock_rejects_second_handle(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = str(Path(tmpdir) / "bot.lock")
            first = runtime_guard.SingleInstanceLock(path)
            second = runtime_guard.SingleInstanceLock(path)
            self.assertTrue(first.acquire())
            try:
                self.assertFalse(second.acquire())
            finally:
                first.release()

    def test_release_ignores_windows_unlock_error(self):
        lock = runtime_guard.SingleInstanceLock("unused")
        handle = MagicMock()
        handle.fileno.return_value = 1
        lock.handle = handle
        with patch("msvcrt.locking", side_effect=PermissionError(13, "denied")):
            lock.release()
        handle.close.assert_called_once()
        self.assertIsNone(lock.handle)

    def test_tracked_tickets_survive_state_reload(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = str(Path(tmpdir) / "state.json")
            with patch.object(runtime_guard.config, "RUNTIME_STATE_FILE", path):
                runtime_guard.save_tracked_tickets({3, 7})
                self.assertEqual(runtime_guard.get_tracked_tickets(), {3, 7})

    def test_daily_equity_baseline_survives_restart_and_resets_next_day(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = str(Path(tmpdir) / "state.json")
            with patch.object(runtime_guard.config, "RUNTIME_STATE_FILE", path):
                first = runtime_guard.get_daily_start_equity(300.0, datetime(2026, 7, 22, 8))
                restarted = runtime_guard.get_daily_start_equity(290.0, datetime(2026, 7, 22, 12))
                next_day = runtime_guard.get_daily_start_equity(295.0, datetime(2026, 7, 23, 1))
                self.assertEqual(first, 300.0)
                self.assertEqual(restarted, 300.0)
                self.assertEqual(next_day, 295.0)


if __name__ == "__main__":
    unittest.main()
