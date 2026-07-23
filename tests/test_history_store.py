import csv
import sys
import tempfile
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from history_store import (
    export_learning_csv,
    import_learning_csv,
    merge_csv_history,
    merge_learning_history,
)


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


class HistoryStoreTests(unittest.TestCase):
    def test_merge_deduplicates_ticket_and_preserves_unique_rows(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            source = root / "old.csv"
            target = root / "new.csv"
            write_csv(source, [
                {"ticket": "1", "profit": "2"},
                {"ticket": "2", "profit": "-1"},
            ])
            write_csv(target, [
                {"ticket": "2", "profit": "-1"},
                {"ticket": "3", "profit": "4"},
            ])
            result = merge_csv_history(source, target, ("ticket",))
            self.assertEqual(result, {"before": 2, "imported": 1, "after": 3})
            with target.open(encoding="utf-8") as handle:
                self.assertEqual(len(list(csv.DictReader(handle))), 3)

    def test_merge_learning_history_does_nothing_for_same_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            self.assertEqual(merge_learning_history(root, root), {})

    def test_export_then_import_supported_experience_csv(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            source = root / "source"
            destination = root / "exports"
            target = root / "target"
            write_csv(source / "closed_trade_log.csv", [{
                "ticket": "10", "signal": "buy", "exit_time": "2026-07-23T10:00:00",
                "profit": "2.0",
            }])
            exported = export_learning_csv(source, destination)
            result = import_learning_csv([exported / "closed_trade_log.csv"], target)
            self.assertEqual(result["closed_trade_log.csv"]["after"], 1)
            self.assertTrue((target / "closed_trade_log.csv").exists())

    def test_import_rejects_unknown_csv(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            unknown = root / "other.csv"
            write_csv(unknown, [{"value": "x"}])
            with self.assertRaises(ValueError):
                import_learning_csv([unknown], root / "target")
