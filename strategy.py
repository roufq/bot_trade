"""
strategy.py
Logika penentuan sinyal entry (OP):
1. Cek tren di timeframe TF_TREND (config.py) -> tentukan bias buy/sell/none
2. Cari titik entry di timeframe TF_ENTRY, searah bias TF_TREND
3. Filter momentum pakai RSI(14) di TF_ENTRY

Catatan: timeframe TF_TREND/TF_ENTRY diatur di config.py -- defaultnya H1/M15,
tapi bisa disesuaikan (misal M1/M1 untuk mode scalping).
"""

from dataclasses import dataclass
from typing import Literal, Optional

import pandas as pd

from indicators import add_all_indicators
import config

Bias = Literal["buy", "sell", "none"]
Signal = Literal["buy", "sell", "none"]


@dataclass
class TradeSignal:
    signal: Signal
    reason: str
    atr_value: Optional[float] = None
    entry_price: Optional[float] = None


def get_trend_bias(df_h1: pd.DataFrame) -> tuple[Bias, str]:
    """
    Menentukan bias arah dari timeframe H1.
    Bias 'buy' jika harga & EMA cepat di atas EMA lambat.
    Bias 'sell' jika sebaliknya.
    """
    df = add_all_indicators(
        df_h1,
        ema_fast=config.EMA_TREND_FAST,
        ema_slow=config.EMA_TREND_SLOW,
        rsi_period=config.RSI_PERIOD,
        atr_period=config.ATR_PERIOD,
    )
    last = df.iloc[-1]
    ema_fast_col = f"ema_{config.EMA_TREND_FAST}"
    ema_slow_col = f"ema_{config.EMA_TREND_SLOW}"

    atr_value = float(last["atr"])
    ema_gap = abs(float(last[ema_fast_col]) - float(last[ema_slow_col]))
    min_gap = atr_value * config.MIN_TREND_ATR_MULTIPLIER
    rsi_value = float(last["rsi"])

    if ema_gap < min_gap:
        return "none", f"{config.TF_TREND}: Sideways, jarak EMA terlalu sempit"
    if last[ema_fast_col] > last[ema_slow_col] and rsi_value >= config.TREND_RSI_CONFIRMATION_THRESHOLD:
        return "buy", f"{config.TF_TREND}: tren naik kuat, EMA{config.EMA_TREND_FAST} > EMA{config.EMA_TREND_SLOW}"
    if last[ema_fast_col] < last[ema_slow_col] and rsi_value <= (100 - config.TREND_RSI_CONFIRMATION_THRESHOLD):
        return "sell", f"{config.TF_TREND}: tren turun kuat, EMA{config.EMA_TREND_FAST} < EMA{config.EMA_TREND_SLOW}"
    return "none", f"{config.TF_TREND}: tren tidak jelas atau RSI belum konfirmasi ({rsi_value:.1f})"


def check_entry_signal(df_m15: pd.DataFrame, bias: Bias) -> TradeSignal:
    """
    Mencari sinyal entry di M15, searah bias dari H1.
    Ada dua jenis sinyal:
    1. Crossover -- EMA cepat baru saja memotong EMA lambat (sinyal awal tren)
    2. Continuation (mode agresif) -- tren sudah searah bias, harga baru saja
       "pullback" mendekati EMA cepat lalu lanjut lagi searah tren. Ini yang
       membuat entry lebih sering muncul dibanding hanya menunggu crossover.
    """
    if bias == "none":
        return TradeSignal(signal="none", reason=f"Tidak ada bias tren dari {config.TF_TREND}")

    df = add_all_indicators(
        df_m15,
        ema_fast=config.EMA_ENTRY_FAST,
        ema_slow=config.EMA_ENTRY_SLOW,
        rsi_period=config.RSI_PERIOD,
        atr_period=config.ATR_PERIOD,
    )

    if len(df) < 2:
        return TradeSignal(signal="none", reason=f"Data {config.TF_ENTRY} tidak cukup untuk cek sinyal")

    prev = df.iloc[-2]
    last = df.iloc[-1]
    ema_fast_col = f"ema_{config.EMA_ENTRY_FAST}"
    ema_slow_col = f"ema_{config.EMA_ENTRY_SLOW}"
    atr_value = float(last["atr"])
    rsi_value = float(last["rsi"])
    close_price = float(last["close"])
    ema_fast_value = float(last[ema_fast_col])

    crossed_up = prev[ema_fast_col] <= prev[ema_slow_col] and last[ema_fast_col] > last[ema_slow_col]
    crossed_down = prev[ema_fast_col] >= prev[ema_slow_col] and last[ema_fast_col] < last[ema_slow_col]

    # Deteksi pelemahan momentum (jika gap EMA menyempit, berpotensi reversal)
    gap_prev = abs(float(prev[ema_fast_col]) - float(prev[ema_slow_col]))
    gap_last = abs(float(last[ema_fast_col]) - float(last[ema_slow_col]))
    momentum_exhausting = gap_last < gap_prev

    # Sinyal continuation: tren sudah searah bias (EMA cepat vs lambat sudah
    # dalam urutan yang benar), dan harga sedang berada dekat EMA cepat --
    # dianggap sedang pullback dalam tren yang sama, bukan awal tren baru.
    near_ema_fast = abs(close_price - ema_fast_value) <= (atr_value * config.CONTINUATION_PULLBACK_ATR_MULTIPLIER)
    close_near_ema = abs(close_price - ema_fast_value) <= (atr_value * config.ENTRY_CLOSE_TO_EMA_MAX_ATR_MULTIPLIER)
    continuation_up = config.ALLOW_TREND_CONTINUATION_ENTRIES and last[ema_fast_col] > last[ema_slow_col] and near_ema_fast and not momentum_exhausting
    continuation_down = config.ALLOW_TREND_CONTINUATION_ENTRIES and last[ema_fast_col] < last[ema_slow_col] and near_ema_fast and not momentum_exhausting

    # Filter Anti-Sideways di Entry:
    # Jika jarak EMA Entry terlalu sempit (kurang dari sekian persen ATR), buang sinyal
    ema_gap = abs(float(last[ema_fast_col]) - float(last[ema_slow_col]))
    min_gap = atr_value * config.MIN_ENTRY_ATR_MULTIPLIER
    if ema_gap < min_gap:
        return TradeSignal(signal="none", reason=f"Sideways {config.TF_ENTRY}: Jarak EMA entry terlalu sempit ({ema_gap:.4f} < {min_gap:.4f})")

    momentum_up = (
        last[ema_fast_col] > last[ema_slow_col]
        and close_price > float(prev["close"])
        and close_price >= last[ema_fast_col]
        and close_near_ema
        and rsi_value >= max(config.RSI_BUY_MIN, config.AGGRESSIVE_ENTRY_RSI_THRESHOLD)
    )
    momentum_down = (
        last[ema_fast_col] < last[ema_slow_col]
        and close_price < float(prev["close"])
        and close_price <= last[ema_fast_col]
        and close_near_ema
        and rsi_value <= min(config.RSI_SELL_MAX, 100 - config.AGGRESSIVE_ENTRY_RSI_THRESHOLD)
    )

    if bias == "buy":
        if crossed_up:
            entry_reason = f"Golden cross {config.TF_ENTRY} searah bias {config.TF_TREND}"
        elif continuation_up:
            entry_reason = f"Continuation: tren naik {config.TF_ENTRY} masih berlanjut, harga pullback ke EMA cepat"
        elif config.ALLOW_AGGRESSIVE_MOMENTUM_ENTRIES and momentum_up:
            entry_reason = f"Momentum entry: tren buy valid di {config.TF_ENTRY} tanpa crossover baru"
        else:
            return TradeSignal(signal="none", reason=f"Belum ada setup buy valid di {config.TF_ENTRY}")

        if not (config.RSI_BUY_MIN <= rsi_value <= config.RSI_BUY_MAX):
            return TradeSignal(
                signal="none",
                reason=f"RSI {rsi_value:.1f} di luar rentang buy ({config.RSI_BUY_MIN}-{config.RSI_BUY_MAX})",
            )
        return TradeSignal(
            signal="buy",
            reason=f"{entry_reason}, RSI dalam rentang valid",
            atr_value=atr_value,
            entry_price=close_price,
        )

    if bias == "sell":
        if crossed_down:
            entry_reason = f"Death cross {config.TF_ENTRY} searah bias {config.TF_TREND}"
        elif continuation_down:
            entry_reason = f"Continuation: tren turun {config.TF_ENTRY} masih berlanjut, harga pullback ke EMA cepat"
        elif config.ALLOW_AGGRESSIVE_MOMENTUM_ENTRIES and momentum_down:
            entry_reason = f"Momentum entry: tren sell valid di {config.TF_ENTRY} tanpa crossover baru"
        else:
            return TradeSignal(signal="none", reason=f"Belum ada setup sell valid di {config.TF_ENTRY}")

        if not (config.RSI_SELL_MIN <= rsi_value <= config.RSI_SELL_MAX):
            return TradeSignal(
                signal="none",
                reason=f"RSI {rsi_value:.1f} di luar rentang sell ({config.RSI_SELL_MIN}-{config.RSI_SELL_MAX})",
            )
        return TradeSignal(
            signal="sell",
            reason=f"{entry_reason}, RSI dalam rentang valid",
            atr_value=atr_value,
            entry_price=close_price,
        )

    return TradeSignal(signal="none", reason="Kondisi tidak terpenuhi")


def evaluate(df_h1: pd.DataFrame, df_m15: pd.DataFrame) -> TradeSignal:
    """Fungsi utama: gabungkan cek bias H1 + cek entry M15."""
    bias, bias_reason = get_trend_bias(df_h1)
    if bias == "none":
        return TradeSignal(signal="none", reason=bias_reason)
    return check_entry_signal(df_m15, bias)
