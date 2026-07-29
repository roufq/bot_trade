"""
trade_logger.py
Mencatat setiap trade dan event sistem ke file CSV.
"""

import csv
import os
import shutil
from datetime import datetime

import pandas as pd
import config

TRADE_FIELDS = [
    "timestamp", "order_id", "position_ticket", "symbol", "signal", "lot_size",
    "entry_time", "entry_price", "sl_price", "tp_price", "atr_value",
    "risk_amount", "h1_ema_gap", "h1_rsi", "h1_atr",
    "m15_ema_gap", "m15_rsi", "m15_atr", "trend_strength",
    "ai_score", "combined_score", "reason", "signal_price", "requested_price",
    "spread_points", "slippage_points",
    "close_to_ema_fast", "ema_gap_ratio", "price_vs_ema_fast", "rsi_diff_m15",
    "h1_ema_slope", "m15_ema_slope", "atr_ratio", "entry_hour", "weekday",
    "ai_expected_r", "learner_expected_r",
    "strategy_source", "strategy_a_signal", "strategy_b_signal",
    "fvg_timeframe", "fvg_lower", "fvg_upper",
    "market_structure_score", "liquidity_score", "snr_score",
    "order_block_score", "supply_demand_score", "displacement_score",
    "premium_discount_score", "candlestick_score", "volume_score", "session_score",
    "signal_side",
]

SYSTEM_FIELDS = ["timestamp", "event", "detail"]
CLOSED_FIELDS = [
    "timestamp", "order_id", "ticket", "symbol", "signal",
    "lot_size", "exit_time", "close_price", "sl_price", "tp_price",
    "atr_value", "risk_amount", "profit", "swap", "commission",
    "balance_after", "reason",
]


def repair_csv_file(path: str, fields: list[str]) -> bool:
    """Perbaiki file CSV yang rusak atau memiliki jumlah kolom yang tidak sesuai."""
    if not os.path.exists(path):
        return False

    rows: list[list[str]] = []
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            if len(row) < len(fields):
                row = row + [""] * (len(fields) - len(row))
            elif len(row) > len(fields):
                row = row[:len(fields)]
            rows.append(row)

    if not rows:
        return False

    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(fields)
        for row in rows[1:]:
            writer.writerow(row)

    return True


def _repair_csv_header(path: str, fields: list[str]) -> None:
    """Perbaiki header CSV lama agar sesuai dengan field yang diharapkan."""
    if not os.path.exists(path):
        return

    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        existing_fields = reader.fieldnames or []

    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            new_row = {field: row.get(field, "") for field in fields}
            writer.writerow(new_row)


def _ensure_file(path: str, fields: list[str]) -> None:
    """Membuat file CSV dengan header jika belum ada, atau perbaiki header lama."""
    if not os.path.exists(path):
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
        return

    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        try:
            rows = [row for row in reader if row]
        except Exception:
            rows = []

    if not rows:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
        return

    header = rows[0]
    malformed = any(len(row) != len(fields) for row in rows[1:])
    if header != fields or malformed:
        repair_csv_file(path, fields)


def ensure_log_files() -> None:
    """Pastikan semua file log ada dan menggunakan schema terbaru."""
    _ensure_file(config.TRADE_LOG_FILE, TRADE_FIELDS)
    _ensure_file(config.CLOSED_TRADE_LOG_FILE, CLOSED_FIELDS)
    _ensure_file(config.SYSTEM_LOG_FILE, SYSTEM_FIELDS)


def clean_trade_log(backup: bool = True) -> dict[str, int]:
    """Bersihkan trade_log.csv dengan menghapus row legacy tanpa position_ticket."""
    ensure_log_files()
    if not os.path.exists(config.TRADE_LOG_FILE):
        return {"total": 0, "kept": 0, "removed": 0}

    df = _read_trade_log_as_dataframe()
    if "position_ticket" not in df.columns:
        return {"total": len(df), "kept": len(df), "removed": 0}

    df["position_ticket"] = df["position_ticket"].fillna("").astype(str).str.strip().replace("nan", "")
    keep_mask = df["position_ticket"] != ""
    kept = int(keep_mask.sum())
    removed = int(len(df) - kept)

    if backup and removed > 0:
        backup_path = f"{config.TRADE_LOG_FILE}.backup"
        if not os.path.exists(backup_path):
            shutil.copyfile(config.TRADE_LOG_FILE, backup_path)

    df.loc[keep_mask, TRADE_FIELDS].to_csv(config.TRADE_LOG_FILE, index=False)
    return {"total": len(df), "kept": kept, "removed": removed}


def _read_trade_log_as_dataframe() -> pd.DataFrame:
    if not os.path.exists(config.TRADE_LOG_FILE):
        return pd.DataFrame(columns=TRADE_FIELDS)

    return pd.read_csv(config.TRADE_LOG_FILE, dtype=str)


def load_closed_trades(start_date: str | None = None, end_date: str | None = None) -> list[dict]:
    """Muat closed trade dari CSV dan filter berdasarkan rentang tanggal opsional."""
    if not os.path.exists(config.CLOSED_TRADE_LOG_FILE):
        return []

    with open(config.CLOSED_TRADE_LOG_FILE, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if start_date is None and end_date is None:
        return rows

    def in_range(row_date_str: str) -> bool:
        try:
            row_date = datetime.fromisoformat(row_date_str).date()
        except ValueError:
            return False
        if start_date is not None and row_date < datetime.fromisoformat(start_date).date():
            return False
        if end_date is not None and row_date > datetime.fromisoformat(end_date).date():
            return False
        return True

    return [row for row in rows if in_range(row.get("exit_time", ""))]


def summarize_closed_trades(start_date: str | None = None, end_date: str | None = None) -> dict:
    """Kalkulasi total profit/loss, win rate, dan ringkasan saldo dari closed trade."""
    rows = load_closed_trades(start_date, end_date)
    if not rows:
        return {
            "total_trades": 0,
            "wins": 0,
            "losses": 0,
            "total_profit": 0.0,
            "total_win_profit": 0.0,
            "total_loss": 0.0,
            "win_rate": 0.0,
            "average_win": 0.0,
            "average_loss": 0.0,
            "start_balance": 0.0,
            "end_balance": 0.0,
        }

    profits = [float(r.get("profit", 0.0) or 0.0) for r in rows]
    wins = [p for p in profits if p > 0]
    losses = [p for p in profits if p <= 0]
    total_profit = sum(profits)
    start_balance = float(rows[0].get("balance_after", 0.0) or 0.0)
    end_balance = float(rows[-1].get("balance_after", 0.0) or 0.0)

    return {
        "total_trades": len(rows),
        "wins": len(wins),
        "losses": len(losses),
        "total_profit": total_profit,
        "total_win_profit": sum(wins),
        "total_loss": sum(losses),
        "win_rate": len(wins) / len(rows) * 100.0 if rows else 0.0,
        "average_win": sum(wins) / len(wins) if wins else 0.0,
        "average_loss": sum(losses) / len(losses) if losses else 0.0,
        "start_balance": start_balance,
        "end_balance": end_balance,
    }


def log_closed_trade(
    order_id: str,
    ticket: int,
    signal: str,
    lot_size: float,
    exit_time: str,
    close_price: float,
    sl_price: float,
    tp_price: float,
    atr_value: float,
    risk_amount: float,
    profit: float,
    balance_after: float,
    swap: float = 0.0,
    commission: float = 0.0,
    reason: str = "",
) -> None:
    """Mencatat satu trade yang baru tertutup untuk pembelajaran adaptif."""
    if not str(order_id).strip() or not str(ticket).strip():
        raise ValueError("Closed trade wajib memiliki entry order_id dan position ticket")
    _ensure_file(config.CLOSED_TRADE_LOG_FILE, CLOSED_FIELDS)
    ticket_text = str(ticket).strip()
    with open(config.CLOSED_TRADE_LOG_FILE, "r", encoding="utf-8", newline="") as f:
        if any(str(row.get("ticket", "")).strip() == ticket_text for row in csv.DictReader(f)):
            return
    row = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "order_id": order_id,
        "ticket": ticket,
        "symbol": config.SYMBOL,
        "signal": signal,
        "lot_size": lot_size,
        "exit_time": exit_time,
        "close_price": close_price,
        "sl_price": sl_price,
        "tp_price": tp_price,
        "atr_value": round(atr_value, 4),
        "risk_amount": round(risk_amount, 2),
        "profit": round(profit, 4),
        "swap": round(swap, 4),
        "commission": round(commission, 4),
        "balance_after": round(balance_after, 2),
        "reason": reason,
    }
    with open(config.CLOSED_TRADE_LOG_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CLOSED_FIELDS)
        writer.writerow(row)


def get_entry_trade_info(order_id: str = "", position_ticket: str | int = "") -> dict:
    """Mencari data entry trade dari order_id atau position_ticket."""
    if not os.path.exists(config.TRADE_LOG_FILE):
        return {"atr_value": 0.0, "risk_amount": 0.0}

    with open(config.TRADE_LOG_FILE, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            return {"atr_value": 0.0, "risk_amount": 0.0}

        for row in reversed(list(reader)):
            if position_ticket and "position_ticket" in row:
                if str(row.get("position_ticket", "")).strip() == str(position_ticket).strip():
                    return {
                        "order_id": row.get("order_id", ""),
                        "signal": row.get("signal", ""),
                        "entry_price": float(row.get("entry_price", 0.0) or 0.0),
                        "sl_price": float(row.get("sl_price", 0.0) or 0.0),
                        "tp_price": float(row.get("tp_price", 0.0) or 0.0),
                        "atr_value": float(row.get("atr_value", 0.0) or 0.0),
                        "risk_amount": float(row.get("risk_amount", 0.0) or 0.0),
                    }
            if order_id and "order_id" in row:
                if str(row.get("order_id", "")).strip() == str(order_id).strip():
                    return {
                        "order_id": row.get("order_id", ""),
                        "signal": row.get("signal", ""),
                        "entry_price": float(row.get("entry_price", 0.0) or 0.0),
                        "sl_price": float(row.get("sl_price", 0.0) or 0.0),
                        "tp_price": float(row.get("tp_price", 0.0) or 0.0),
                        "atr_value": float(row.get("atr_value", 0.0) or 0.0),
                        "risk_amount": float(row.get("risk_amount", 0.0) or 0.0),
                    }

    return {"atr_value": 0.0, "risk_amount": 0.0}


def log_trade(order_id: str, position_ticket: str | int, signal: str, lot_size: float, entry_time: str,
              entry_price: float, sl_price: float, tp_price: float, atr_value: float,
              risk_amount: float, h1_ema_gap: float, h1_rsi: float, h1_atr: float,
              m15_ema_gap: float, m15_rsi: float, m15_atr: float,
              trend_strength: float, ai_score: float, combined_score: float,
              reason: str, signal_price: float = 0.0, requested_price: float = 0.0,
              spread_points: float = 0.0, slippage_points: float = 0.0,
              feature_values: dict | None = None, ai_expected_r: float | None = None,
              learner_expected_r: float = 0.0, strategy_source: str = "A_ONLY",
              strategy_a_signal: str = "", strategy_b_signal: str = "",
              fvg_timeframe: str = "", fvg_lower: float | None = None,
              fvg_upper: float | None = None) -> None:
    """Mencatat satu trade yang baru dieksekusi."""
    _ensure_file(config.TRADE_LOG_FILE, TRADE_FIELDS)
    feature_values = feature_values or {}
    row = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "order_id": order_id,
        "position_ticket": str(position_ticket) if position_ticket is not None else "",
        "symbol": config.SYMBOL,
        "signal": signal,
        "lot_size": lot_size,
        "entry_time": entry_time,
        "entry_price": entry_price,
        "sl_price": sl_price,
        "tp_price": tp_price,
        "atr_value": round(atr_value, 4),
        "risk_amount": round(risk_amount, 2),
        "h1_ema_gap": round(h1_ema_gap, 8),
        "h1_rsi": round(h1_rsi, 4),
        "h1_atr": round(h1_atr, 4),
        "m15_ema_gap": round(m15_ema_gap, 8),
        "m15_rsi": round(m15_rsi, 4),
        "m15_atr": round(m15_atr, 4),
        "trend_strength": round(trend_strength, 4),
        "ai_score": round(ai_score, 4),
        "ai_expected_r": round(ai_expected_r, 4) if ai_expected_r is not None else "",
        "learner_expected_r": round(learner_expected_r, 4),
        "strategy_source": strategy_source,
        "strategy_a_signal": strategy_a_signal,
        "strategy_b_signal": strategy_b_signal,
        "fvg_timeframe": fvg_timeframe,
        "fvg_lower": round(fvg_lower, 8) if fvg_lower is not None else "",
        "fvg_upper": round(fvg_upper, 8) if fvg_upper is not None else "",
        "combined_score": round(combined_score, 4),
        "reason": reason,
        "signal_price": signal_price,
        "requested_price": requested_price,
        "spread_points": round(spread_points, 2),
        "slippage_points": round(slippage_points, 2),
        "close_to_ema_fast": feature_values.get("close_to_ema_fast", ""),
        "ema_gap_ratio": feature_values.get("ema_gap_ratio", ""),
        "price_vs_ema_fast": feature_values.get("price_vs_ema_fast", ""),
        "rsi_diff_m15": feature_values.get("rsi_diff_m15", ""),
        "h1_ema_slope": feature_values.get("h1_ema_slope", ""),
        "m15_ema_slope": feature_values.get("m15_ema_slope", ""),
        "atr_ratio": feature_values.get("atr_ratio", ""),
        "entry_hour": feature_values.get("entry_hour", ""),
        "weekday": feature_values.get("weekday", ""),
        "market_structure_score": feature_values.get("market_structure_score", 0.0),
        "liquidity_score": feature_values.get("liquidity_score", 0.0),
        "snr_score": feature_values.get("snr_score", 0.0),
        "order_block_score": feature_values.get("order_block_score", 0.0),
        "supply_demand_score": feature_values.get("supply_demand_score", 0.0),
        "displacement_score": feature_values.get("displacement_score", 0.0),
        "premium_discount_score": feature_values.get("premium_discount_score", 0.0),
        "candlestick_score": feature_values.get("candlestick_score", 0.0),
        "volume_score": feature_values.get("volume_score", 0.0),
        "session_score": feature_values.get("session_score", 0.0),
        "signal_side": feature_values.get("signal_side", 0.0),
    }
    with open(config.TRADE_LOG_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=TRADE_FIELDS)
        writer.writerow(row)


def log_system_event(event: str, detail: str = "") -> None:
    """Mencatat event sistem: start, stop, error, drawdown limit, dll."""
    _ensure_file(config.SYSTEM_LOG_FILE, SYSTEM_FIELDS)
    row = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "event": event,
        "detail": detail,
    }
    with open(config.SYSTEM_LOG_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=SYSTEM_FIELDS)
        writer.writerow(row)
