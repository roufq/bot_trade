"""Penyatuan histori trading dari instalasi/project lama secara aman."""

from __future__ import annotations

import csv
import shutil
import tempfile
from datetime import datetime
from pathlib import Path


LEARNING_FILES = {
    "trade_log.csv": ("position_ticket", "order_id"),
    "closed_trade_log.csv": ("ticket",),
    "shadow_signal_log.csv": ("signal_time", "signal", "setup"),
}

REQUIRED_COLUMNS = {
    "trade_log.csv": {"order_id", "position_ticket", "signal", "entry_time"},
    "closed_trade_log.csv": {"ticket", "signal", "exit_time", "profit"},
    "shadow_signal_log.csv": {"signal_time", "signal", "decision"},
}


def _read_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not path.exists() or path.stat().st_size == 0:
        return [], []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), [dict(row) for row in reader]


def _row_key(row: dict[str, str], key_fields: tuple[str, ...]) -> tuple[str, ...]:
    values = tuple(str(row.get(field, "")).strip() for field in key_fields)
    if any(values):
        return values
    # Baris lama tanpa key jangan sampai saling menimpa.
    return ("__row__", repr(sorted(row.items())))


def merge_csv_history(
    source: Path,
    target: Path,
    key_fields: tuple[str, ...],
    backup_dir: Path | None = None,
) -> dict[str, int]:
    source_fields, source_rows = _read_rows(source)
    target_fields, target_rows = _read_rows(target)
    fields = list(target_fields)
    fields.extend(field for field in source_fields if field not in fields)
    if not fields:
        return {"before": 0, "imported": 0, "after": 0}

    merged: dict[tuple[str, ...], dict[str, str]] = {}
    for row in target_rows + source_rows:
        key = _row_key(row, key_fields)
        existing = merged.get(key)
        # Jika ticket sama, pertahankan baris yang mempunyai data paling lengkap.
        if existing is None or sum(bool(v) for v in row.values()) > sum(bool(v) for v in existing.values()):
            merged[key] = row

    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and backup_dir is not None:
        backup_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, backup_dir / target.name)

    rows = list(merged.values())
    timestamp_field = "timestamp" if "timestamp" in fields else "signal_time"
    rows.sort(key=lambda row: str(row.get(timestamp_field, "")))
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", newline="", delete=False, dir=target.parent, suffix=".tmp"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
        temporary = Path(handle.name)
    temporary.replace(target)
    return {
        "before": len(target_rows),
        "imported": max(0, len(rows) - len(target_rows)),
        "after": len(rows),
    }


def merge_learning_history(source_dir: Path, target_dir: Path) -> dict[str, dict[str, int]]:
    source_dir = source_dir.resolve()
    target_dir = target_dir.resolve()
    if source_dir == target_dir:
        return {}
    backup_dir = target_dir / "history_backups" / datetime.now().strftime("%Y%m%d_%H%M%S")
    results = {}
    for filename, keys in LEARNING_FILES.items():
        results[filename] = merge_csv_history(
            source_dir / filename,
            target_dir / filename,
            keys,
            backup_dir=backup_dir,
        )
    return results


def import_learning_csv(files: list[Path], target_dir: Path) -> dict[str, dict[str, int]]:
    """Import CSV pilihan pengguna; hanya nama dan skema histori resmi diterima."""
    target_dir = target_dir.resolve()
    backup_dir = target_dir / "history_backups" / datetime.now().strftime("%Y%m%d_%H%M%S")
    results = {}
    for source in files:
        filename = source.name.lower()
        if filename not in LEARNING_FILES:
            raise ValueError(
                f"{source.name} bukan file pengalaman yang didukung. "
                f"Pilih: {', '.join(LEARNING_FILES)}"
            )
        fields, _ = _read_rows(source)
        missing = REQUIRED_COLUMNS[filename] - set(fields)
        if missing:
            raise ValueError(
                f"{source.name} tidak valid; kolom wajib tidak ada: {', '.join(sorted(missing))}"
            )
        results[filename] = merge_csv_history(
            source,
            target_dir / filename,
            LEARNING_FILES[filename],
            backup_dir=backup_dir,
        )
    return results


def export_learning_csv(source_dir: Path, destination_dir: Path) -> Path:
    """Ekspor CSV pengalaman tanpa kredensial, system log, atau data konfigurasi."""
    source_dir = source_dir.resolve()
    destination_dir = destination_dir.resolve()
    export_dir = destination_dir / f"AITradingExperience_{datetime.now():%Y%m%d_%H%M%S}"
    export_dir.mkdir(parents=True, exist_ok=False)
    copied = 0
    for filename in LEARNING_FILES:
        source = source_dir / filename
        if source.exists() and source.stat().st_size:
            shutil.copy2(source, export_dir / filename)
            copied += 1
    if copied == 0:
        export_dir.rmdir()
        raise ValueError("Belum ada CSV pengalaman yang dapat diekspor.")
    return export_dir
