"""Audit log trading sebelum learner atau model ML memakai datanya."""

import os
import pandas as pd

import config
import learner


def audit() -> dict:
    result = {"valid": False, "reason": "file closed trade tidak ada", "rows": 0}
    if not os.path.exists(config.CLOSED_TRADE_LOG_FILE):
        return result
    try:
        df = pd.read_csv(config.CLOSED_TRADE_LOG_FILE, low_memory=False)
    except Exception as exc:
        result["reason"] = f"CSV tidak dapat dibaca: {exc}"
        return result
    valid, reason = learner.validate_closed_trade_history(df)
    result.update({"valid": valid, "reason": reason, "rows": len(df)})
    if "ticket" in df:
        result["unique_tickets"] = int(df["ticket"].nunique(dropna=True))
    if "profit" in df:
        profit = pd.to_numeric(df["profit"], errors="coerce")
        result["unique_profit_values"] = int(profit.nunique(dropna=True))
        result["win_rate"] = float((profit > 0).mean()) if len(profit) else 0.0
    return result


if __name__ == "__main__":
    report = audit()
    print("VALID" if report["valid"] else "INVALID", report)
