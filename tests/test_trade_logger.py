import csv
import sys
import tempfile
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import trade_logger


class TradeLoggerRepairTests(unittest.TestCase):
    def test_repair_log_with_malformed_reason_and_missing_columns(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "trade_log.csv"
            header = trade_logger.TRADE_FIELDS
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(header)
                writer.writerow([
                    "2026-07-21T10:00:00",
                    "order-1",
                    "",
                    "XAUUSD.vx",
                    "buy",
                    "0.01",
                    "2026-07-21T10:00:00",
                    "4010.00",
                    "4009.50",
                    "4011.50",
                    "1.10",
                    "1.20",
                    "0.11",
                    "55.0",
                    "1.10",
                    "0.22",
                    "56.0",
                    "1.11",
                    "0.33",
                    "0.55",
                    "0.66",
                    "Continuation: tren naik, harga pullback, RSI valid",
                ])
                writer.writerow([
                    "2026-07-21T10:01:00",
                    "order-2",
                    "",
                    "XAUUSD.vx",
                    "sell",
                    "0.02",
                    "2026-07-21T10:01:00",
                    "4009.00",
                    "4008.50",
                    "4010.00",
                    "1.20",
                    "1.30",
                    "0.12",
                    "44.0",
                    "1.20",
                ])

            repaired = trade_logger.repair_csv_file(path, trade_logger.TRADE_FIELDS)
            self.assertTrue(repaired)

            with path.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.reader(handle))

            self.assertEqual(len(rows[0]), len(header))
            self.assertEqual(len(rows[1]), len(header))
            self.assertEqual(len(rows[2]), len(header))
            self.assertIn("Continuation: tren naik, harga pullback, RSI valid", rows[1][-1])
            self.assertEqual(rows[2][-1], "")

    def test_clean_trade_log_removes_rows_without_position_ticket(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "trade_log.csv"
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(trade_logger.TRADE_FIELDS)
                writer.writerow([
                    "2026-07-21T10:00:00",
                    "order-1",
                    "",
                    "XAUUSD.vx",
                    "buy",
                    "0.01",
                    "2026-07-21T10:00:00",
                    "4010.00",
                    "4009.50",
                    "4011.50",
                    "1.10",
                    "1.20",
                    "0.11",
                    "55.0",
                    "1.10",
                    "0.22",
                    "56.0",
                    "1.11",
                    "0.33",
                    "0.55",
                    "0.66",
                    "",
                ])
                writer.writerow([
                    "2026-07-21T10:01:00",
                    "order-2",
                    "12345",
                    "XAUUSD.vx",
                    "sell",
                    "0.02",
                    "2026-07-21T10:01:00",
                    "4009.00",
                    "4008.50",
                    "4010.00",
                    "1.20",
                    "1.30",
                    "0.12",
                    "44.0",
                    "1.20",
                    "0.33",
                    "0.44",
                    "0.55",
                    "0.66",
                    "valid",
                ])

            old_trade_file = trade_logger.config.TRADE_LOG_FILE
            trade_logger.config.TRADE_LOG_FILE = str(path)
            try:
                result = trade_logger.clean_trade_log(backup=False)
            finally:
                trade_logger.config.TRADE_LOG_FILE = old_trade_file

            self.assertEqual(result["removed"], 1)
            self.assertEqual(result["kept"], 1)
            with path.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.reader(handle))
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[1][2], "12345")

    def test_log_closed_trade_is_idempotent_by_ticket(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "closed.csv"
            old_path = trade_logger.config.CLOSED_TRADE_LOG_FILE
            trade_logger.config.CLOSED_TRADE_LOG_FILE = str(path)
            kwargs = dict(
                order_id="order-1", ticket=123, signal="buy", lot_size=0.01,
                exit_time="2026-07-21T10:00:00", close_price=4011.0,
                sl_price=4009.0, tp_price=4012.0, atr_value=1.0,
                risk_amount=1.0, profit=2.0, balance_after=102.0,
            )
            try:
                trade_logger.log_closed_trade(**kwargs)
                trade_logger.log_closed_trade(**kwargs)
            finally:
                trade_logger.config.CLOSED_TRADE_LOG_FILE = old_path
            with path.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 1)

    def test_entry_lookup_returns_original_order_and_levels(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "trade.csv"
            old_path = trade_logger.config.TRADE_LOG_FILE
            trade_logger.config.TRADE_LOG_FILE = str(path)
            try:
                trade_logger.log_trade(
                    "entry-order", "999", "sell", 0.01, "2026-07-21T10:00:00",
                    4010.0, 4012.0, 4007.0, 1.0, 2.0,
                    0.1, 45.0, 1.0, 0.2, 44.0, 1.1, 0.3, 0.0, 0.5, "test",
                )
                info = trade_logger.get_entry_trade_info(position_ticket=999)
            finally:
                trade_logger.config.TRADE_LOG_FILE = old_path
            self.assertEqual(info["order_id"], "entry-order")
            self.assertEqual(info["signal"], "sell")
            self.assertEqual(info["sl_price"], 4012.0)


if __name__ == "__main__":
    unittest.main()
