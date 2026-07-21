import csv
import datetime
import os
import shutil

SOURCE_FILE = "trade_log.csv"
BACKUP_FILE = f"trade_log.csv.bak.{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
TARGET_FILE = "trade_log.csv"

NEW_COLUMNS = [
    "timestamp",
    "order_id",
    "symbol",
    "signal",
    "lot_size",
    "entry_time",
    "entry_price",
    "sl_price",
    "tp_price",
    "atr_value",
    "risk_amount",
    "h1_ema_gap",
    "h1_rsi",
    "h1_atr",
    "m15_ema_gap",
    "m15_rsi",
    "m15_atr",
    "trend_strength",
    "reason",
]

OLD_COLUMNS = [
    "timestamp",
    "symbol",
    "signal",
    "lot_size",
    "entry_price",
    "sl_price",
    "tp_price",
    "atr_value",
    "risk_amount",
    "reason",
]

if not os.path.exists(SOURCE_FILE):
    raise FileNotFoundError(f"File sumber tidak ditemukan: {SOURCE_FILE}")

shutil.copy2(SOURCE_FILE, BACKUP_FILE)
print(f"Backup dibuat: {BACKUP_FILE}")

rows = []
with open(SOURCE_FILE, "r", encoding="utf-8", newline="") as f:
    reader = csv.reader(f)
    header = next(reader, None)
    if header is None:
        raise ValueError("File kosong atau header tidak ditemukan")

    if header == NEW_COLUMNS:
        print("File sudah dalam schema baru. Akan menormalisasi data dan menulis ulang file.")

    for idx, row in enumerate(reader, start=1):
        if not row:
            continue

        if len(row) == len(OLD_COLUMNS):
            row_data = dict(zip(OLD_COLUMNS, row))
            order_id = f"legacy_{idx}"
            entry_time = row_data["timestamp"]
            new_row = {
                "timestamp": row_data["timestamp"],
                "order_id": order_id,
                "symbol": row_data["symbol"],
                "signal": row_data["signal"],
                "lot_size": row_data["lot_size"],
                "entry_time": entry_time,
                "entry_price": row_data["entry_price"],
                "sl_price": row_data["sl_price"],
                "tp_price": row_data["tp_price"],
                "atr_value": row_data["atr_value"],
                "risk_amount": row_data["risk_amount"],
                "h1_ema_gap": "0.0",
                "h1_rsi": "0.0",
                "h1_atr": "0.0",
                "m15_ema_gap": "0.0",
                "m15_rsi": "0.0",
                "m15_atr": "0.0",
                "trend_strength": "0.0",
                "reason": row_data["reason"],
            }
        elif len(row) >= len(NEW_COLUMNS):
            # Jika row lebih panjang karena reason mengandung koma, gabungkan sisa kolom ke field reason.
            row_data = row[: len(NEW_COLUMNS) - 1]
            reason_parts = row[len(NEW_COLUMNS) - 1 :]
            row_data.append(",".join(reason_parts).strip())
            new_row = dict(zip(NEW_COLUMNS, row_data))
            if not new_row.get("order_id"):
                new_row["order_id"] = f"legacy_{idx}"
            if not new_row.get("entry_time"):
                new_row["entry_time"] = new_row["timestamp"]
        else:
            # Jika schema tidak jelas, coba deteksi dari header dan isi kosong untuk sisa field.
            minimal = dict(zip(header, row))
            order_id = minimal.get("order_id") or f"legacy_{idx}"
            entry_time = minimal.get("entry_time") or minimal.get("timestamp")
            new_row = {
                "timestamp": minimal.get("timestamp", ""),
                "order_id": order_id,
                "symbol": minimal.get("symbol", ""),
                "signal": minimal.get("signal", ""),
                "lot_size": minimal.get("lot_size", ""),
                "entry_time": entry_time,
                "entry_price": minimal.get("entry_price", ""),
                "sl_price": minimal.get("sl_price", ""),
                "tp_price": minimal.get("tp_price", ""),
                "atr_value": minimal.get("atr_value", ""),
                "risk_amount": minimal.get("risk_amount", ""),
                "h1_ema_gap": minimal.get("h1_ema_gap", "0.0"),
                "h1_rsi": minimal.get("h1_rsi", "0.0"),
                "h1_atr": minimal.get("h1_atr", "0.0"),
                "m15_ema_gap": minimal.get("m15_ema_gap", "0.0"),
                "m15_rsi": minimal.get("m15_rsi", "0.0"),
                "m15_atr": minimal.get("m15_atr", "0.0"),
                "trend_strength": minimal.get("trend_strength", "0.0"),
                "reason": minimal.get("reason", ""),
            }

        rows.append(new_row)

with open(TARGET_FILE, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=NEW_COLUMNS)
    writer.writeheader()
    writer.writerows(rows)

print(f"Konversi selesai: {len(rows)} baris ditulis ke {TARGET_FILE}")
print(f"Backup file: {BACKUP_FILE}")
