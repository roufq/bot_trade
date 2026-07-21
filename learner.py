"""
learner.py
Lapisan adaptif untuk menyesuaikan risiko dan keputusan entry berdasarkan
riwayat trading dan kondisi pasar saat ini.

Fokusnya bukan model ML berat, tapi sebuah engine pembelajaran ringan yang:
- membaca hasil trade tertutup untuk mengidentifikasi win rate dan loss streak
- mengukur kekuatan tren dari data H1/M15
- menyesuaikan persentase risiko berdasarkan performa dan kondisi pasar
- menolak entry ketika confidence terlalu rendah
"""

from dataclasses import dataclass
import os
from typing import Optional

import pandas as pd

import config
from indicators import add_all_indicators


@dataclass
class LearningDecision:
    risk_percent: float
    score: float
    reason: str
    win_rate: float
    loss_streak: int
    trend_strength: float
    recent_trades: int


def validate_closed_trade_history(df: pd.DataFrame) -> tuple[bool, str]:
    """Tolak histori yang terlalu kecil, duplikat, atau hasilnya tidak bervariasi."""
    if df.empty:
        return False, "histori closed trade kosong"
    required = {"ticket", "profit", "timestamp"}
    missing = required - set(df.columns)
    if missing:
        return False, f"kolom wajib hilang: {sorted(missing)}"
    if len(df) < config.LEARNING_MIN_VALID_CLOSED_TRADES:
        return False, f"baru {len(df)} trade valid"

    tickets = df["ticket"].fillna("").astype(str).str.strip()
    if (tickets == "").any():
        return False, "ticket kosong ditemukan"
    duplicate_ratio = float(tickets.duplicated().mean())
    if duplicate_ratio > config.LEARNING_MAX_DUPLICATE_TICKET_RATIO:
        return False, f"ticket duplikat {duplicate_ratio:.1%}"

    profit = pd.to_numeric(df["profit"], errors="coerce")
    if profit.isna().any():
        return False, "profit non-numerik ditemukan"
    if profit.round(4).nunique() < config.LEARNING_MIN_PROFIT_VARIATION:
        return False, "variasi profit tidak wajar"
    if not ((profit > 0).any() and (profit <= 0).any()):
        return False, "histori hanya berisi satu kelas hasil"
    return True, "valid"


def load_recent_closed_trades(max_trades: int = config.LEARNING_HISTORICAL_TRADES_WINDOW) -> pd.DataFrame:
    if not os.path.exists(config.CLOSED_TRADE_LOG_FILE):
        return pd.DataFrame()

    df = pd.read_csv(config.CLOSED_TRADE_LOG_FILE, parse_dates=["timestamp"], low_memory=False)
    if df.empty:
        return df

    valid, _ = validate_closed_trade_history(df)
    if not valid:
        return pd.DataFrame(columns=df.columns)
    return df.tail(max_trades)


def calculate_trade_metrics(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "win_rate": 0.0,
            "loss_streak": 0,
            "average_profit": 0.0,
            "average_loss": 0.0,
            "recent_trades": 0,
        }

    profit = df["profit"].astype(float)
    winners = profit[profit > 0]
    losers = profit[profit <= 0]
    win_rate = len(winners) / len(profit) if len(profit) > 0 else 0.0
    average_profit = winners.mean() if not winners.empty else 0.0
    average_loss = losers.mean() if not losers.empty else 0.0

    loss_streak = 0
    for value in reversed(profit.tolist()):
        if value < 0:
            loss_streak += 1
        else:
            break

    return {
        "win_rate": win_rate,
        "loss_streak": loss_streak,
        "average_profit": average_profit,
        "average_loss": average_loss,
        "recent_trades": len(profit),
    }


def estimate_trend_strength(df: pd.DataFrame, ema_fast: int, ema_slow: int) -> float:
    if df is None or len(df) < max(ema_fast, ema_slow, config.ATR_PERIOD) + 1:
        return 0.0

    df_indicators = add_all_indicators(
        df,
        ema_fast=ema_fast,
        ema_slow=ema_slow,
        rsi_period=config.RSI_PERIOD,
        atr_period=config.ATR_PERIOD,
    )
    last = df_indicators.iloc[-1]
    atr_value = float(last["atr"])
    ema_gap = abs(float(last[f"ema_{ema_fast}"]) - float(last[f"ema_{ema_slow}"]))
    if atr_value <= 0:
        return 0.0

    strength = min(1.0, ema_gap / (atr_value * config.LEARNING_TREND_STRENGTH_DIVISOR))
    return float(strength)


def estimate_market_score(df_h1: pd.DataFrame, df_m15: pd.DataFrame) -> float:
    h1_strength = estimate_trend_strength(df_h1, config.EMA_TREND_FAST, config.EMA_TREND_SLOW)
    m15_strength = estimate_trend_strength(df_m15, config.EMA_ENTRY_FAST, config.EMA_ENTRY_SLOW)
    return float((h1_strength + m15_strength) / 2.0)


def build_adaptive_risk_percent(
    equity: float,
    recent_metrics: dict,
    market_score: float,
    current_drawdown_pct: float,
) -> tuple[float, str]:
    base_risk = config.RISK_PERCENT_PER_TRADE
    risk = base_risk
    reason_parts = []

    if recent_metrics["recent_trades"] == 0:
        reason_parts.append("Belum ada histori trade tertutup, pakai risiko dasar")
    else:
        if recent_metrics["loss_streak"] >= config.LEARNING_LOSS_STREAK_THRESHOLD:
            risk *= config.LEARNING_LOSS_STREAK_MULTIPLIER
            reason_parts.append(
                f"Loss streak {recent_metrics['loss_streak']} -> kurangi risiko"
            )
        elif recent_metrics["win_rate"] >= config.LEARNING_HIGH_WINRATE_THRESHOLD:
            risk *= config.LEARNING_WIN_STREAK_MULTIPLIER
            reason_parts.append(
                f"Win rate tinggi {recent_metrics['win_rate']:.0%} -> tingkatkan risiko"
            )
        else:
            reason_parts.append(f"Win rate {recent_metrics['win_rate']:.0%}")

    if market_score >= config.LEARNING_STRONG_MARKET_THRESHOLD:
        risk *= config.LEARNING_STRONG_MARKET_MULTIPLIER
        reason_parts.append(f"Kondisi pasar kuat (score {market_score:.2f})")
    elif market_score <= config.LEARNING_WEAK_MARKET_THRESHOLD:
        risk *= config.LEARNING_WEAK_MARKET_MULTIPLIER
        reason_parts.append(f"Kondisi pasar lemah (score {market_score:.2f})")
    else:
        reason_parts.append(f"Kondisi pasar moderat (score {market_score:.2f})")

    if current_drawdown_pct >= config.MAX_DAILY_DRAWDOWN_PERCENT * 0.5:
        risk *= config.LEARNING_HIGH_DRAWDOWN_MULTIPLIER
        reason_parts.append(
            f"Drawdown harian {current_drawdown_pct:.1f}% -> risiko ekstra dipotong"
        )

    min_risk = config.RISK_PERCENT_PER_TRADE * config.LEARNING_MIN_RISK_MULTIPLIER
    max_risk = config.RISK_PERCENT_PER_TRADE * config.LEARNING_MAX_RISK_MULTIPLIER
    risk = max(min_risk, min(risk, max_risk))

    return risk, "; ".join(reason_parts)


def compute_entry_score(recent_metrics: dict, market_score: float) -> float:
    if recent_metrics["recent_trades"] == 0:
        return float(market_score * 0.5 + 0.25)

    score = (
        0.4 * recent_metrics["win_rate"]
        + 0.4 * market_score
        + 0.2 * max(0.0, 1.0 - recent_metrics["loss_streak"] / config.LEARNING_MAX_LOSS_STREAK_FOR_SCORE)
    )
    return float(max(0.0, min(1.0, score)))


def decide(
    df_h1: pd.DataFrame,
    df_m15: pd.DataFrame,
    current_drawdown_pct: float,
) -> LearningDecision:
    recent_closed = load_recent_closed_trades()
    metrics = calculate_trade_metrics(recent_closed)
    market_score = estimate_market_score(df_h1, df_m15)
    risk_percent, reason = build_adaptive_risk_percent(
        equity=0.0,
        recent_metrics=metrics,
        market_score=market_score,
        current_drawdown_pct=current_drawdown_pct,
    )
    score = compute_entry_score(metrics, market_score)

    if recent_closed.empty:
        reason = "Belum ada histori tertutup, adaptasi risiko berjalan dengan konservatif"

    return LearningDecision(
        risk_percent=risk_percent,
        score=score,
        reason=reason,
        win_rate=metrics["win_rate"],
        loss_streak=metrics["loss_streak"],
        trend_strength=market_score,
        recent_trades=metrics["recent_trades"],
    )
