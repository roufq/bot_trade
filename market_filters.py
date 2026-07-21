"""Filter spread, volatilitas, blackout berita manual, cooldown, dan loss streak."""

from datetime import datetime, timedelta

import pandas as pd

import config
from indicators import calculate_atr


def spread_metrics(ask: float, bid: float, point: float, atr: float) -> tuple[float, float]:
    spread = max(0.0, ask - bid)
    points = spread / point if point > 0 else float("inf")
    atr_ratio = spread / atr if atr > 0 else float("inf")
    return points, atr_ratio


def check_spread(ask: float, bid: float, point: float, atr: float) -> tuple[bool, str, float]:
    points, atr_ratio = spread_metrics(ask, bid, point, atr)
    allowed = points <= config.MAX_SPREAD_POINTS and atr_ratio <= config.MAX_SPREAD_ATR_RATIO
    return allowed, f"spread={points:.1f} points, {atr_ratio:.1%} ATR", points


def check_volatility(df: pd.DataFrame) -> tuple[bool, str]:
    if not config.VOLATILITY_FILTER_ENABLED:
        return True, "filter volatilitas nonaktif"
    atr = calculate_atr(df, config.ATR_PERIOD).dropna()
    if len(atr) < 20:
        return False, "data ATR belum cukup"
    current = float(atr.iloc[-1])
    median = float(atr.tail(50).median())
    ratio = current / median if median > 0 else float("inf")
    allowed = config.MIN_ATR_TO_MEDIAN_RATIO <= ratio <= config.MAX_ATR_TO_MEDIAN_RATIO
    return allowed, f"ATR/median={ratio:.2f}"


def in_news_blackout(now: datetime | None = None) -> tuple[bool, str]:
    now = now or datetime.now()
    current_minutes = now.hour * 60 + now.minute
    for window in config.NEWS_BLACKOUT_WINDOWS:
        try:
            start_text, end_text = window.split("-", 1)
            sh, sm = map(int, start_text.split(":"))
            eh, em = map(int, end_text.split(":"))
            start, end = sh * 60 + sm, eh * 60 + em
        except (ValueError, TypeError):
            continue
        inside = start <= current_minutes < end if start <= end else (current_minutes >= start or current_minutes < end)
        if inside:
            return True, f"blackout berita manual {window}"
    return False, ""


def recent_trade_guard(df_closed: pd.DataFrame, now: datetime | None = None) -> tuple[bool, str]:
    if df_closed is None or df_closed.empty:
        return True, ""
    now = now or datetime.now()
    df = df_closed.copy()
    df["profit"] = pd.to_numeric(df["profit"], errors="coerce")
    df["exit_time"] = pd.to_datetime(df["exit_time"], errors="coerce")
    df = df.dropna(subset=["profit", "exit_time"]).sort_values("exit_time")
    if df.empty:
        return True, ""
    latest = df.iloc[-1]
    cooldown = config.COOLDOWN_AFTER_LOSS_SECONDS if latest["profit"] < 0 else config.COOLDOWN_AFTER_WIN_SECONDS
    resume_at = latest["exit_time"].to_pydatetime() + timedelta(seconds=cooldown)
    if now < resume_at:
        return False, f"cooldown sampai {resume_at:%H:%M:%S}"

    loss_streak = 0
    for value in reversed(df["profit"].tolist()):
        if value < 0:
            loss_streak += 1
        else:
            break
    if loss_streak >= config.MAX_CONSECUTIVE_LOSSES:
        streak_resume = latest["exit_time"].to_pydatetime() + timedelta(minutes=config.LOSS_STREAK_COOLDOWN_MINUTES)
        if now < streak_resume:
            return False, f"loss streak {loss_streak}, jeda sampai {streak_resume:%H:%M:%S}"
    return True, ""
