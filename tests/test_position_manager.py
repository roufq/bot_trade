from types import SimpleNamespace
import sys
from pathlib import Path
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import position_manager


class PositionManagerTests(unittest.TestCase):
    def test_break_even_never_worsens_buy_stop(self):
        pos = SimpleNamespace(ticket=1, symbol="X", type=0, price_open=100.0, sl=99.0, tp=105.0)
        with patch.object(position_manager.mt5_connector, "modify_position_sltp", return_value={"success": True}) as modify:
            events = position_manager.manage(
                [pos], atr=1.0, ask=101.6, bid=101.5,
                symbol_info={"point": 0.01, "trade_tick_size": 0.01},
            )
        self.assertTrue(events)
        self.assertGreater(modify.call_args.args[2], pos.sl)
        self.assertLess(modify.call_args.args[2], 101.5)


if __name__ == "__main__":
    unittest.main()
