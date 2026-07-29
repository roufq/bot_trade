import sys
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import mt5_connector


class ClosedDealLookupTests(unittest.TestCase):
    def test_filters_and_aggregates_only_requested_position(self):
        position = 123
        entry = SimpleNamespace(
            entry=0, position_id=position, time_msc=1, volume=0.01,
            price=100.0, profit=0.0, swap=0.0, commission=0.0, fee=0.0,
            _asdict=lambda: {"entry": 0, "position_id": position},
        )
        exit_deal = SimpleNamespace(
            entry=1, position_id=position, time_msc=2, volume=0.01,
            price=99.0, profit=-1.0, swap=-0.1, commission=-0.05, fee=0.0,
            _asdict=lambda: {
                "entry": 1, "position_id": position, "type": 1,
                "price": 99.0, "volume": 0.01, "profit": -1.0,
            },
        )
        fake_mt5 = SimpleNamespace(
            DEAL_ENTRY_OUT=1,
            history_deals_get=lambda **kwargs: [entry, exit_deal]
            if kwargs == {"position": position} else None,
        )
        with patch.object(mt5_connector, "mt5", fake_mt5):
            result = mt5_connector.get_closed_deal_by_position(position, max_retries=1)
        self.assertEqual(result["profit"], -1.0)
        self.assertEqual(result["volume"], 0.01)
        self.assertEqual(result["commission"], -0.05)


class ClosePositionTests(unittest.TestCase):
    def test_close_targets_ticket_with_opposite_order(self):
        requests = []
        result = SimpleNamespace(retcode=10009, order=21, deal=22, price=100.5, comment="done")
        fake_mt5 = SimpleNamespace(
            POSITION_TYPE_BUY=0, ORDER_TYPE_BUY=0, ORDER_TYPE_SELL=1,
            ORDER_FILLING_FOK=0, ORDER_FILLING_IOC=1, ORDER_FILLING_RETURN=2,
            TRADE_ACTION_DEAL=1, ORDER_TIME_GTC=0, TRADE_RETCODE_DONE=10009,
            symbol_info_tick=lambda symbol: SimpleNamespace(bid=100.5, ask=100.6),
            symbol_info=lambda symbol: SimpleNamespace(filling_mode=1),
            order_check=lambda request: SimpleNamespace(retcode=0, comment="ok"),
            order_send=lambda request: requests.append(request) or result,
            last_error=lambda: (0, "ok"),
        )
        opened = SimpleNamespace(
            ticket=123, symbol="XAUUSD.vx", volume=0.01, type=0,
        )
        with patch.object(mt5_connector, "mt5", fake_mt5):
            closed = mt5_connector.close_position(opened)
        self.assertTrue(closed["success"])
        self.assertEqual(requests[0]["position"], 123)
        self.assertEqual(requests[0]["type"], fake_mt5.ORDER_TYPE_SELL)
