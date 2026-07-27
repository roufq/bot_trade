import sys
import tempfile
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import runtime_guard


class RuntimeGuardTests(unittest.TestCase):
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
