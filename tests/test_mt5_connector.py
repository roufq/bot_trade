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
