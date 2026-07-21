import sys
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

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

    def test_tracked_tickets_survive_state_reload(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = str(Path(tmpdir) / "state.json")
            with patch.object(runtime_guard.config, "RUNTIME_STATE_FILE", path):
                runtime_guard.save_tracked_tickets({3, 7})
                self.assertEqual(runtime_guard.get_tracked_tickets(), {3, 7})


if __name__ == "__main__":
    unittest.main()
