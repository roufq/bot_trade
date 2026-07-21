"""Kill-switch berdasarkan performa rolling dan deviasi loss aktual."""

import pandas as pd

import config


def evaluate(df_closed: pd.DataFrame) -> tuple[bool, str, dict]:
    if df_closed is None or df_closed.empty:
        return True, "", {}
    df = df_closed.tail(config.ROLLING_PERFORMANCE_WINDOW).copy()
    df["profit"] = pd.to_numeric(df["profit"], errors="coerce")
    df["risk_amount"] = pd.to_numeric(df.get("risk_amount"), errors="coerce")
    df = df.dropna(subset=["profit"])
    if len(df) < config.ROLLING_PERFORMANCE_MIN_TRADES:
        return True, "", {"trades": len(df)}
    wins = df.loc[df["profit"] > 0, "profit"]
    losses = df.loc[df["profit"] <= 0, "profit"]
    gross_loss = abs(float(losses.sum()))
    profit_factor = float(wins.sum()) / gross_loss if gross_loss > 0 else float("inf")
    expectancy = float(df["profit"].mean())
    metrics = {"trades": len(df), "profit_factor": profit_factor, "expectancy": expectancy}
    if profit_factor < config.MIN_ROLLING_PROFIT_FACTOR:
        return False, f"rolling profit factor {profit_factor:.2f} < {config.MIN_ROLLING_PROFIT_FACTOR:.2f}", metrics
    if expectancy < config.MIN_ROLLING_EXPECTANCY:
        return False, f"rolling expectancy {expectancy:.2f} < {config.MIN_ROLLING_EXPECTANCY:.2f}", metrics
    valid_risk = df[(df["profit"] < 0) & (df["risk_amount"] > 0)]
    if not valid_risk.empty:
        ratio = (-valid_risk["profit"] / valid_risk["risk_amount"]).max()
        metrics["max_loss_to_risk"] = float(ratio)
        if ratio > config.MAX_REALIZED_LOSS_TO_PLANNED_RISK:
            return False, f"loss aktual {ratio:.2f}x planned risk", metrics
    return True, "", metrics
