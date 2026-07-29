"""Modul analisis price-action yang independen dan dapat dipelajari terpisah."""

from dataclasses import dataclass, field
from datetime import time
from typing import Literal

import pandas as pd

from indicators import calculate_atr

Direction = Literal["buy", "sell", "none"]


@dataclass(frozen=True)
class TechnicalSignal:
    code: str
    name: str
    direction: Direction
    score: float
    reason: str
    primary: bool = False
    metadata: dict = field(default_factory=dict)


TECHNIQUE_CODES = {
    "C": "market_structure",
    "D": "liquidity",
    "E": "snr",
    "F": "order_block",
    "G": "supply_demand",
    "H": "displacement",
    "I": "premium_discount",
    "J": "candlestick",
    "K": "volume",
    "L": "session",
}


def _neutral(code: str, reason: str) -> TechnicalSignal:
    return TechnicalSignal(code, TECHNIQUE_CODES[code], "none", 0.0, reason)


def _work(df: pd.DataFrame, minimum: int = 20) -> pd.DataFrame | None:
    required = {"open", "high", "low", "close"}
    if df is None or len(df) < minimum or not required.issubset(df.columns):
        return None
    result = df.sort_values("time").reset_index(drop=True).copy() if "time" in df else df.reset_index(drop=True).copy()
    result["atr"] = calculate_atr(result, 14)
    return result if pd.notna(result.iloc[-1]["atr"]) else None


def _pivots(df: pd.DataFrame, window: int = 2) -> tuple[list[tuple[int, float]], list[tuple[int, float]]]:
    highs, lows = [], []
    for index in range(window, len(df) - window):
        high_window = df["high"].iloc[index - window:index + window + 1]
        low_window = df["low"].iloc[index - window:index + window + 1]
        if float(df.iloc[index]["high"]) == float(high_window.max()):
            highs.append((index, float(df.iloc[index]["high"])))
        if float(df.iloc[index]["low"]) == float(low_window.min()):
            lows.append((index, float(df.iloc[index]["low"])))
    return highs, lows


def market_structure(df: pd.DataFrame) -> TechnicalSignal:
    work = _work(df)
    if work is None:
        return _neutral("C", "data market structure belum cukup")
    highs, lows = _pivots(work.iloc[:-1])
    if len(highs) < 2 or len(lows) < 2:
        return _neutral("C", "swing terkonfirmasi belum cukup")
    close = float(work.iloc[-1]["close"])
    atr = float(work.iloc[-1]["atr"])
    last_high, prior_high = highs[-1][1], highs[-2][1]
    last_low, prior_low = lows[-1][1], lows[-2][1]
    if close > last_high:
        score = 1.0 if last_high > prior_high and last_low > prior_low else 0.8
        return TechnicalSignal("C", TECHNIQUE_CODES["C"], "buy", score, "bullish BOS/CHoCH di atas swing high", True, {"level": last_high})
    if close < last_low:
        score = 1.0 if last_high < prior_high and last_low < prior_low else 0.8
        return TechnicalSignal("C", TECHNIQUE_CODES["C"], "sell", score, "bearish BOS/CHoCH di bawah swing low", True, {"level": last_low})
    if last_high > prior_high and last_low > prior_low and close >= last_low + atr * 0.25:
        return TechnicalSignal("C", TECHNIQUE_CODES["C"], "buy", 0.55, "struktur HH/HL aktif", True)
    if last_high < prior_high and last_low < prior_low and close <= last_high - atr * 0.25:
        return TechnicalSignal("C", TECHNIQUE_CODES["C"], "sell", 0.55, "struktur LH/LL aktif", True)
    return _neutral("C", "struktur pasar campuran")


def liquidity(df: pd.DataFrame) -> TechnicalSignal:
    work = _work(df)
    if work is None:
        return _neutral("D", "data liquidity belum cukup")
    highs, lows = _pivots(work.iloc[:-1])
    last = work.iloc[-1]
    atr = float(last["atr"])
    tolerance = atr * 0.12
    if lows:
        level = lows[-1][1]
        if float(last["low"]) < level - tolerance and float(last["close"]) > level:
            return TechnicalSignal("D", TECHNIQUE_CODES["D"], "buy", 1.0, "sell-side liquidity sweep dan reclaim", True, {"level": level})
    if highs:
        level = highs[-1][1]
        if float(last["high"]) > level + tolerance and float(last["close"]) < level:
            return TechnicalSignal("D", TECHNIQUE_CODES["D"], "sell", 1.0, "buy-side liquidity sweep dan reclaim", True, {"level": level})
    return _neutral("D", "belum ada liquidity sweep terkonfirmasi")


def snr(df: pd.DataFrame) -> TechnicalSignal:
    work = _work(df)
    if work is None:
        return _neutral("E", "data SNR belum cukup")
    history, last = work.iloc[-31:-1], work.iloc[-1]
    support, resistance = float(history["low"].min()), float(history["high"].max())
    tolerance = float(last["atr"]) * 0.25
    bullish = float(last["close"]) > float(last["open"])
    if float(last["low"]) <= support + tolerance and bullish and float(last["close"]) > support:
        return TechnicalSignal("E", TECHNIQUE_CODES["E"], "buy", 0.85, "rejection pada support", True, {"level": support})
    if float(last["high"]) >= resistance - tolerance and not bullish and float(last["close"]) < resistance:
        return TechnicalSignal("E", TECHNIQUE_CODES["E"], "sell", 0.85, "rejection pada resistance", True, {"level": resistance})
    if float(last["close"]) > resistance + tolerance:
        return TechnicalSignal("E", TECHNIQUE_CODES["E"], "buy", 0.75, "breakout resistance", True, {"level": resistance})
    if float(last["close"]) < support - tolerance:
        return TechnicalSignal("E", TECHNIQUE_CODES["E"], "sell", 0.75, "breakdown support", True, {"level": support})
    return _neutral("E", "harga tidak bereaksi pada SNR utama")


def order_block(df: pd.DataFrame) -> TechnicalSignal:
    work = _work(df, 25)
    if work is None:
        return _neutral("F", "data order block belum cukup")
    atr = float(work.iloc[-1]["atr"])
    last = work.iloc[-1]
    for index in range(len(work) - 3, max(1, len(work) - 18), -1):
        origin, move = work.iloc[index - 1], work.iloc[index]
        move_body = abs(float(move["close"]) - float(move["open"]))
        if move_body < atr * 0.9:
            continue
        if float(origin["close"]) < float(origin["open"]) and float(move["close"]) > float(move["open"]):
            lower, upper = float(origin["low"]), float(origin["high"])
            if float(last["low"]) <= upper and float(last["close"]) > upper:
                return TechnicalSignal("F", TECHNIQUE_CODES["F"], "buy", 0.8, "mitigasi bullish order block", True, {"lower": lower, "upper": upper})
        if float(origin["close"]) > float(origin["open"]) and float(move["close"]) < float(move["open"]):
            lower, upper = float(origin["low"]), float(origin["high"])
            if float(last["high"]) >= lower and float(last["close"]) < lower:
                return TechnicalSignal("F", TECHNIQUE_CODES["F"], "sell", 0.8, "mitigasi bearish order block", True, {"lower": lower, "upper": upper})
    return _neutral("F", "belum ada mitigasi order block")


def supply_demand(df: pd.DataFrame) -> TechnicalSignal:
    work = _work(df, 25)
    if work is None:
        return _neutral("G", "data supply/demand belum cukup")
    last, atr = work.iloc[-1], float(work.iloc[-1]["atr"])
    for index in range(len(work) - 4, max(2, len(work) - 22), -1):
        base = work.iloc[index - 2:index + 1]
        departure = work.iloc[index + 1]
        base_range = float(base["high"].max() - base["low"].min())
        if base_range > atr * 1.5:
            continue
        lower, upper = float(base["low"].min()), float(base["high"].max())
        if float(departure["close"]) > upper + atr * 0.6 and float(last["low"]) <= upper and float(last["close"]) > upper:
            return TechnicalSignal("G", TECHNIQUE_CODES["G"], "buy", 0.75, "retest demand zone dengan departure kuat", True, {"lower": lower, "upper": upper})
        if float(departure["close"]) < lower - atr * 0.6 and float(last["high"]) >= lower and float(last["close"]) < lower:
            return TechnicalSignal("G", TECHNIQUE_CODES["G"], "sell", 0.75, "retest supply zone dengan departure kuat", True, {"lower": lower, "upper": upper})
    return _neutral("G", "belum ada retest supply/demand valid")


def displacement(df: pd.DataFrame) -> TechnicalSignal:
    work = _work(df)
    if work is None:
        return _neutral("H", "data displacement belum cukup")
    last = work.iloc[-1]
    full_range = max(float(last["high"] - last["low"]), 1e-12)
    body = float(last["close"] - last["open"])
    if abs(body) >= float(last["atr"]) * 1.1 and abs(body) / full_range >= 0.65:
        direction = "buy" if body > 0 else "sell"
        return TechnicalSignal("H", TECHNIQUE_CODES["H"], direction, 0.75, f"displacement {direction} kuat")
    return _neutral("H", "tidak ada displacement kuat")


def premium_discount(df: pd.DataFrame) -> TechnicalSignal:
    work = _work(df)
    if work is None:
        return _neutral("I", "data dealing range belum cukup")
    history = work.iloc[-51:-1]
    low, high = float(history["low"].min()), float(history["high"].max())
    width = high - low
    if width <= 0:
        return _neutral("I", "dealing range tidak valid")
    location = (float(work.iloc[-1]["close"]) - low) / width
    if location <= 0.35:
        return TechnicalSignal("I", TECHNIQUE_CODES["I"], "buy", 0.45, "harga berada di discount", metadata={"location": location})
    if location >= 0.65:
        return TechnicalSignal("I", TECHNIQUE_CODES["I"], "sell", 0.45, "harga berada di premium", metadata={"location": location})
    return _neutral("I", "harga dekat equilibrium")


def candlestick(df: pd.DataFrame) -> TechnicalSignal:
    work = _work(df)
    if work is None:
        return _neutral("J", "data candlestick belum cukup")
    prev, last = work.iloc[-2], work.iloc[-1]
    prev_low, prev_high = sorted((float(prev["open"]), float(prev["close"])))
    last_low, last_high = sorted((float(last["open"]), float(last["close"])))
    if float(last["close"]) > float(last["open"]) and float(prev["close"]) < float(prev["open"]) and last_low <= prev_low and last_high >= prev_high:
        return TechnicalSignal("J", TECHNIQUE_CODES["J"], "buy", 0.7, "bullish engulfing")
    if float(last["close"]) < float(last["open"]) and float(prev["close"]) > float(prev["open"]) and last_low <= prev_low and last_high >= prev_high:
        return TechnicalSignal("J", TECHNIQUE_CODES["J"], "sell", 0.7, "bearish engulfing")
    body = abs(float(last["close"] - last["open"]))
    lower_wick = min(float(last["open"]), float(last["close"])) - float(last["low"])
    upper_wick = float(last["high"]) - max(float(last["open"]), float(last["close"]))
    if lower_wick >= max(body * 2.0, float(last["atr"]) * 0.25):
        return TechnicalSignal("J", TECHNIQUE_CODES["J"], "buy", 0.6, "bullish rejection candle")
    if upper_wick >= max(body * 2.0, float(last["atr"]) * 0.25):
        return TechnicalSignal("J", TECHNIQUE_CODES["J"], "sell", 0.6, "bearish rejection candle")
    return _neutral("J", "tidak ada pola candle terkonfirmasi")


def volume(df: pd.DataFrame) -> TechnicalSignal:
    work = _work(df)
    if work is None or "volume" not in work:
        return _neutral("K", "data volume belum tersedia")
    baseline = float(work["volume"].iloc[-21:-1].median())
    last = work.iloc[-1]
    if baseline > 0 and float(last["volume"]) >= baseline * 1.5:
        direction = "buy" if float(last["close"]) > float(last["open"]) else "sell"
        return TechnicalSignal("K", TECHNIQUE_CODES["K"], direction, 0.6, f"ekspansi tick-volume {direction}")
    return _neutral("K", "tick-volume tidak ekspansif")


def session_context(df: pd.DataFrame) -> TechnicalSignal:
    if df is None or df.empty or "time" not in df:
        return _neutral("L", "waktu sesi tidak tersedia")
    timestamp = pd.to_datetime(df.sort_values("time").iloc[-1]["time"])
    current = timestamp.time()
    if time(7, 0) <= current < time(10, 0):
        return TechnicalSignal("L", TECHNIQUE_CODES["L"], "none", 0.6, "London active window")
    if time(12, 0) <= current < time(16, 0):
        return TechnicalSignal("L", TECHNIQUE_CODES["L"], "none", 0.7, "New York active window")
    return TechnicalSignal("L", TECHNIQUE_CODES["L"], "none", 0.25, "off-session context")


def evaluate_all(df_context: pd.DataFrame, df_entry: pd.DataFrame) -> list[TechnicalSignal]:
    """Evaluasi setiap teknik secara independen; tidak ada voting di fungsi ini."""
    return [
        market_structure(df_context), liquidity(df_entry), snr(df_context),
        order_block(df_context), supply_demand(df_context), displacement(df_entry),
        premium_discount(df_context), candlestick(df_entry), volume(df_entry),
        session_context(df_entry),
    ]
