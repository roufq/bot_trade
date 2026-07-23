"""Catat hasil virtual sinyal AI yang diterima dan ditolak tanpa mengirim order."""

import csv
import os
from datetime import datetime

import pandas as pd

import config

FIELDS = [
    "signal_time", "signal", "setup", "entry_price", "sl_price", "tp_price",
    "ai_probability", "ai_expected_r", "learner_r", "decision", "status",
    "resolved_time", "result_r",
]


def _read() -> list[dict]:
    if not os.path.exists(config.SHADOW_SIGNAL_LOG_FILE):
        return []
    with open(config.SHADOW_SIGNAL_LOG_FILE, "r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write(rows: list[dict]) -> None:
    temporary = f"{config.SHADOW_SIGNAL_LOG_FILE}.tmp"
    with open(temporary, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows({key: row.get(key, "") for key in FIELDS} for row in rows)
    os.replace(temporary, config.SHADOW_SIGNAL_LOG_FILE)


def record(signal_time, signal: str, setup: str, entry_price: float, atr: float,
           ai_probability: float | None, ai_expected_r: float | None,
           learner_r: float, decision: str) -> None:
    if not entry_price or atr <= 0 or signal not in {"buy", "sell"}:
        return
    timestamp = str(pd.to_datetime(signal_time))
    rows = _read()
    if any(row.get("signal_time") == timestamp and row.get("signal") == signal for row in rows):
        return
    sl_distance = atr * config.SL_ATR_MULTIPLIER
    tp_distance = atr * config.TP_ATR_MULTIPLIER
    sl = entry_price - sl_distance if signal == "buy" else entry_price + sl_distance
    tp = entry_price + tp_distance if signal == "buy" else entry_price - tp_distance
    rows.append({
        "signal_time": timestamp, "signal": signal, "setup": setup,
        "entry_price": entry_price, "sl_price": sl, "tp_price": tp,
        "ai_probability": "" if ai_probability is None else ai_probability,
        "ai_expected_r": "" if ai_expected_r is None else ai_expected_r,
        "learner_r": learner_r, "decision": decision, "status": "pending",
        "resolved_time": "", "result_r": "",
    })
    _write(rows)


def resolve(candles: pd.DataFrame) -> int:
    """Selesaikan simulasi SL/TP; bila keduanya kena satu candle, hitung loss."""
    rows = _read()
    if not rows or candles is None or candles.empty:
        return 0
    frame = candles.copy()
    frame["time"] = pd.to_datetime(frame["time"])
    resolved = 0
    for row in rows:
        if row.get("status") != "pending":
            continue
        future = frame[frame["time"] > pd.to_datetime(row["signal_time"])]
        signal, sl, tp = row["signal"], float(row["sl_price"]), float(row["tp_price"])
        for _, candle in future.iterrows():
            sl_hit = float(candle["low"]) <= sl if signal == "buy" else float(candle["high"]) >= sl
            tp_hit = float(candle["high"]) >= tp if signal == "buy" else float(candle["low"]) <= tp
            if sl_hit or tp_hit:
                row["status"] = "resolved"
                row["resolved_time"] = str(candle["time"])
                row["result_r"] = -1.0 if sl_hit else config.TP_ATR_MULTIPLIER / config.SL_ATR_MULTIPLIER
                resolved += 1
                break
    if resolved:
        _write(rows)
    return resolved
