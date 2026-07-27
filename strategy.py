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
    strategy_source: str = "A_ONLY"
    strategy_a_signal: Signal = "none"
    strategy_b_signal: Signal = "none"
    fvg_timeframe: str = ""
    fvg_lower: Optional[float] = None
    fvg_upper: Optional[float] = None


@dataclass(frozen=True)
class FVGZone:
    direction: Literal["buy", "sell"]
    lower: float
    upper: float
    timeframe: str
    created_at: object
    age_bars: int


def detect_fvg_zones(
    df: pd.DataFrame,
    timeframe: str,
    max_age_bars: int,
) -> list[FVGZone]:
    """Deteksi FVG tiga-candle yang masih aktif, hanya dari candle tertutup."""
    required = {"time", "open", "high", "low", "close"}
    if df is None or len(df) < config.ATR_PERIOD + 3 or not required.issubset(df.columns):
        return []

    work = df.sort_values("time").reset_index(drop=True).copy()
    work["atr"] = add_all_indicators(
        work, config.EMA_ENTRY_FAST, config.EMA_ENTRY_SLOW,
        config.RSI_PERIOD, config.ATR_PERIOD,
    )["atr"]
    zones: list[FVGZone] = []
    start = max(2, len(work) - max_age_bars - 2)
    for index in range(start, len(work)):
        first = work.iloc[index - 2]
        third = work.iloc[index]
        atr = float(third["atr"])
        if not pd.notna(atr) or atr <= 0:
            continue
        age = len(work) - 1 - index
        candidates: list[tuple[str, float, float]] = []
        if float(third["low"]) > float(first["high"]):
            candidates.append(("buy", float(first["high"]), float(third["low"])))
        if float(third["high"]) < float(first["low"]):
            candidates.append(("sell", float(third["high"]), float(first["low"])))
        for direction, lower, upper in candidates:
            if upper - lower < atr * config.FVG_MIN_GAP_ATR:
                continue
            later = work.iloc[index + 1:]
            # Zona dianggap selesai setelah sisi jauh telah disentuh penuh.
            filled = (
                (not later.empty and float(later["low"].min()) <= lower)
                if direction == "buy"
                else (not later.empty and float(later["high"].max()) >= upper)
            )
            if not filled:
                zones.append(FVGZone(direction, lower, upper, timeframe, third["time"], age))
    return zones


def _overlap_zone(first: FVGZone, second: FVGZone) -> Optional[FVGZone]:
    if first.direction != second.direction:
        return None
    lower, upper = max(first.lower, second.lower), min(first.upper, second.upper)
    if lower > upper:
        return None
    return FVGZone(first.direction, lower, upper, "H1+M15", second.created_at, min(first.age_bars, second.age_bars))


def _m1_rejection(df_m1: pd.DataFrame, zone: FVGZone) -> bool:
    if df_m1 is None or df_m1.empty:
        return False
    candle = df_m1.sort_values("time").iloc[-1]
    high, low = float(candle["high"]), float(candle["low"])
    if low > zone.upper or high < zone.lower:
        return False
    open_price, close = float(candle["open"]), float(candle["close"])
    full_range = max(high - low, 1e-12)
    body_ratio = abs(close - open_price) / full_range
    midpoint = (zone.lower + zone.upper) / 2.0
    if body_ratio < config.FVG_REJECTION_MIN_BODY_RATIO:
        return False
    if zone.direction == "buy":
        return close > open_price and close >= midpoint
    return close < open_price and close <= midpoint


def evaluate_fvg(df_h1: pd.DataFrame, df_m15: pd.DataFrame, df_m1: pd.DataFrame) -> TradeSignal:
    """Strategi B: zona FVG H1/M15 dan trigger rejection pada M1."""
    h1_zones = detect_fvg_zones(df_h1, "H1", config.FVG_MAX_AGE_H1_BARS)
    m15_zones = detect_fvg_zones(df_m15, "M15", config.FVG_MAX_AGE_M15_BARS)
    overlaps = [zone for h1 in h1_zones for m15 in m15_zones if (zone := _overlap_zone(h1, m15))]
    candidates = overlaps + sorted(h1_zones + m15_zones, key=lambda zone: (zone.age_bars, zone.timeframe))
    triggered = [zone for zone in candidates if _m1_rejection(df_m1, zone)]
    directions = {zone.direction for zone in triggered}
    if len(directions) > 1:
        return TradeSignal("none", "Strategi B konflik: FVG buy dan sell sama-sama terpicu", strategy_source="NONE")
    if not triggered:
        return TradeSignal("none", "Strategi B netral: belum ada rejection M1 pada FVG aktif", strategy_source="NONE")
    zone = triggered[0]
    atr_series = add_all_indicators(
        df_m1, config.EMA_ENTRY_FAST, config.EMA_ENTRY_SLOW,
        config.RSI_PERIOD, config.ATR_PERIOD,
    )["atr"].dropna()
    atr = float(atr_series.iloc[-1]) if not atr_series.empty else None
    close = float(df_m1.sort_values("time").iloc[-1]["close"])
    return TradeSignal(
        zone.direction,
        f"FVG {zone.timeframe} {zone.direction} [{zone.lower:.4f}-{zone.upper:.4f}] + rejection M1",
        atr_value=atr,
        entry_price=close,
        strategy_source="B_ONLY",
        strategy_b_signal=zone.direction,
        fvg_timeframe=zone.timeframe,
        fvg_lower=zone.lower,
        fvg_upper=zone.upper,
    )


def combine_signals(signal_a: TradeSignal, signal_b: TradeSignal) -> TradeSignal:
    """Gabungkan A/B: netral mengizinkan solo, konflik membatalkan entry."""
    a, b = signal_a.signal, signal_b.signal
    if a != "none" and b != "none" and a != b:
        return TradeSignal(
            "none", f"Konflik strategi: A={a}, B={b}; entry dibatalkan",
            strategy_source="CONFLICT", strategy_a_signal=a, strategy_b_signal=b,
        )
    if a != "none" and b == "none":
        signal_a.strategy_source = "A_ONLY"
        signal_a.strategy_a_signal = a
        signal_a.strategy_b_signal = "none"
        signal_a.reason = f"A_ONLY: {signal_a.reason}; B netral"
        return signal_a
    if b != "none" and a == "none":
        signal_b.strategy_source = "B_ONLY"
        signal_b.strategy_a_signal = "none"
        signal_b.strategy_b_signal = b
        signal_b.reason = f"B_ONLY: A netral; {signal_b.reason}"
        return signal_b
    if a != "none" and a == b:
        return TradeSignal(
            a,
            f"A_PLUS_B: {signal_a.reason}; {signal_b.reason}",
            atr_value=signal_a.atr_value or signal_b.atr_value,
            entry_price=signal_b.entry_price or signal_a.entry_price,
            strategy_source="A_PLUS_B",
            strategy_a_signal=a,
            strategy_b_signal=b,
            fvg_timeframe=signal_b.fvg_timeframe,
            fvg_lower=signal_b.fvg_lower,
            fvg_upper=signal_b.fvg_upper,
        )
    return TradeSignal("none", "Strategi A dan B netral", strategy_source="NONE")


def risk_multiplier_for(strategy_source: str) -> float:
    """Confluence tidak menggandakan risiko; sinyal solo diperkecil."""
    if strategy_source in {"A_ONLY", "B_ONLY"}:
        return config.STRATEGY_SOLO_RISK_MULTIPLIER
    return 1.0


def evaluate_hybrid(
    df_a_trend: pd.DataFrame,
    df_a_entry: pd.DataFrame,
    df_h1: pd.DataFrame,
    df_m15: pd.DataFrame,
    df_m1: pd.DataFrame,
) -> TradeSignal:
    signal_a = evaluate(df_a_trend, df_a_entry) if config.STRATEGY_A_ENABLED else TradeSignal("none", "A nonaktif")
    signal_b = evaluate_fvg(df_h1, df_m15, df_m1) if config.STRATEGY_B_ENABLED else TradeSignal("none", "B nonaktif")
    return combine_signals(signal_a, signal_b)


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
