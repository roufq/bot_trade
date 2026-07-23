"""Kill-switch berdasarkan performa rolling dan deviasi loss aktual."""

from datetime import datetime, timedelta

import pandas as pd

import config


def evaluate(df_closed: pd.DataFrame, now: datetime | None = None) -> tuple[bool, str, dict]:
    now = now or datetime.now()
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
    valid_r = df[df["risk_amount"] > 0]
    expectancy_r = float((valid_r["profit"] / valid_r["risk_amount"]).mean()) if not valid_r.empty else 0.0
    metrics = {
        "trades": len(df), "profit_factor": profit_factor,
        "expectancy": expectancy, "expectancy_r": expectancy_r,
    }
    degraded_reasons = []
    if profit_factor < config.MIN_ROLLING_PROFIT_FACTOR:
        degraded_reasons.append(f"PF {profit_factor:.2f}")
    if expectancy < config.MIN_ROLLING_EXPECTANCY:
        degraded_reasons.append(f"expectancy {expectancy:+.2f}")
    if degraded_reasons:
        metrics["degraded"] = True
        time_column = "exit_time" if "exit_time" in df else "timestamp" if "timestamp" in df else None
        latest_time = pd.to_datetime(df.iloc[-1][time_column], errors="coerce") if time_column else pd.NaT
        resume_at = (
            latest_time.to_pydatetime() + timedelta(minutes=config.ROLLING_KILL_SWITCH_COOLDOWN_MINUTES)
            if pd.notna(latest_time) else now + timedelta(minutes=config.ROLLING_KILL_SWITCH_COOLDOWN_MINUTES)
        )
        if now < resume_at:
            return False, (f"rolling melemah ({', '.join(degraded_reasons)}); "
                           f"mode probe mulai {resume_at:%H:%M:%S}"), metrics
        metrics["probe_mode"] = True
    valid_risk = df[(df["profit"] < 0) & (df["risk_amount"] > 0)]
    if not valid_risk.empty:
        ratio = (-valid_risk["profit"] / valid_risk["risk_amount"]).max()
        metrics["max_loss_to_risk"] = float(ratio)
        if ratio > config.MAX_REALIZED_LOSS_TO_PLANNED_RISK:
            worst_index = (-valid_risk["profit"] / valid_risk["risk_amount"]).idxmax()
            time_column = "exit_time" if "exit_time" in valid_risk else "timestamp"
            loss_time = pd.to_datetime(valid_risk.loc[worst_index, time_column], errors="coerce")
            blocked_until = loss_time.to_pydatetime() + timedelta(minutes=config.OVERSIZED_LOSS_COOLDOWN_MINUTES) if pd.notna(loss_time) else now
            if now < blocked_until:
                return False, (f"loss aktual {ratio:.2f}x planned risk; cooldown sampai "
                               f"{blocked_until:%H:%M:%S}"), metrics
            metrics["oversized_loss_cooldown_complete"] = True
    reason = "mode probe: " + ", ".join(degraded_reasons) if degraded_reasons else ""
    return True, reason, metrics
