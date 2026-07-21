"""Ringkasan performa trading dari log lokal yang sudah tervalidasi."""

import os
import pandas as pd

import config


def build_report() -> dict:
    if not os.path.exists(config.CLOSED_TRADE_LOG_FILE):
        return {"total_trades": 0}
    closed = pd.read_csv(config.CLOSED_TRADE_LOG_FILE, low_memory=False)
    if closed.empty:
        return {"total_trades": 0}
    profit = pd.to_numeric(closed["profit"], errors="coerce").dropna()
    wins, losses = profit[profit > 0], profit[profit <= 0]
    gross_profit, gross_loss = float(wins.sum()), abs(float(losses.sum()))
    loss_streak = max_loss_streak = 0
    for value in profit.tolist():
        loss_streak = loss_streak + 1 if value < 0 else 0
        max_loss_streak = max(max_loss_streak, loss_streak)
    balance = pd.to_numeric(closed.get("balance_after"), errors="coerce").dropna()
    if balance.empty:
        max_drawdown = 0.0
    else:
        peak = balance.cummax()
        max_drawdown = float(((peak - balance) / peak.replace(0, pd.NA) * 100).max() or 0.0)

    report = {
        "total_trades": int(len(profit)),
        "wins": int(len(wins)),
        "losses": int(len(losses)),
        "win_rate_percent": float((profit > 0).mean() * 100),
        "net_profit": float(profit.sum()),
        "profit_factor": gross_profit / gross_loss if gross_loss > 0 else float("inf"),
        "expectancy": float(profit.mean()),
        "average_win": float(wins.mean()) if not wins.empty else 0.0,
        "average_loss": float(losses.mean()) if not losses.empty else 0.0,
        "max_loss_streak": max_loss_streak,
        "max_closed_balance_drawdown_percent": max_drawdown,
    }
    if os.path.exists(config.TRADE_LOG_FILE):
        entries = pd.read_csv(config.TRADE_LOG_FILE, low_memory=False)
        for column in ["spread_points", "slippage_points"]:
            if column in entries:
                values = pd.to_numeric(entries[column], errors="coerce").dropna()
                report[f"average_{column}"] = float(values.mean()) if not values.empty else 0.0
    return report


if __name__ == "__main__":
    for key, value in build_report().items():
        print(f"{key}: {value:.4f}" if isinstance(value, float) else f"{key}: {value}")
