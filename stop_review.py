"""Audit pasca-SL untuk membedakan wick stop dari kesalahan arah."""

import csv
import os

import pandas as pd

import config

FIELDS = [
    "ticket", "signal", "exit_time", "entry_price", "sl_price", "tp_price",
    "risk_distance", "status", "classification", "reviewed_time",
    "post_stop_mfe_r", "post_stop_adverse_r",
]


def _read() -> list[dict]:
    if not os.path.exists(config.STOP_REVIEW_LOG_FILE):
        return []
    with open(config.STOP_REVIEW_LOG_FILE, "r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write(rows: list[dict]) -> None:
    os.makedirs(os.path.dirname(config.STOP_REVIEW_LOG_FILE), exist_ok=True)
    temporary = config.STOP_REVIEW_LOG_FILE + ".tmp"
    with open(temporary, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in FIELDS} for row in rows)
    os.replace(temporary, config.STOP_REVIEW_LOG_FILE)


def record(ticket, signal: str, exit_time: str, entry_price: float, sl_price: float, tp_price: float) -> None:
    rows = _read()
    if any(str(row.get("ticket")) == str(ticket) for row in rows):
        return
    risk = abs(float(entry_price) - float(sl_price))
    if signal not in {"buy", "sell"} or risk <= 0:
        return
    rows.append({
        "ticket": ticket, "signal": signal, "exit_time": exit_time,
        "entry_price": entry_price, "sl_price": sl_price, "tp_price": tp_price,
        "risk_distance": risk, "status": "pending", "classification": "",
        "reviewed_time": "", "post_stop_mfe_r": "", "post_stop_adverse_r": "",
    })
    _write(rows)


def resolve(candles: pd.DataFrame) -> int:
    rows = _read()
    if not rows or candles is None or candles.empty:
        return 0
    frame = candles.copy()
    frame["time"] = pd.to_datetime(frame["time"])
    resolved = 0
    for row in rows:
        if row.get("status") != "pending":
            continue
        future = frame[frame["time"] > pd.to_datetime(row["exit_time"])].head(config.STOP_REVIEW_HORIZON_BARS)
        if len(future) < config.STOP_REVIEW_HORIZON_BARS:
            continue
        signal = row["signal"]
        entry, tp, risk = float(row["entry_price"]), float(row["tp_price"]), float(row["risk_distance"])
        if signal == "buy":
            favorable = float(future["high"].max()) - entry
            adverse = entry - float(future["low"].min())
            tp_recovered = float(future["high"].max()) >= tp
        else:
            favorable = entry - float(future["low"].min())
            adverse = float(future["high"].max()) - entry
            tp_recovered = float(future["low"].min()) <= tp
        mfe_r, adverse_r = max(0.0, favorable / risk), max(0.0, adverse / risk)
        classification = "wick_stop_tp_recovered" if tp_recovered else "wick_stop_recovered" if mfe_r >= 1.0 else "direction_wrong"
        row.update({
            "status": "resolved", "classification": classification,
            "reviewed_time": str(future.iloc[-1]["time"]),
            "post_stop_mfe_r": round(mfe_r, 4), "post_stop_adverse_r": round(adverse_r, 4),
        })
        resolved += 1
    if resolved:
        _write(rows)
    return resolved
