"""
indicators.py
Fungsi perhitungan indikator teknikal murni menggunakan pandas.
Input selalu berupa DataFrame dengan kolom: open, high, low, close.
"""

import pandas as pd


def calculate_ema(df: pd.DataFrame, period: int, column: str = "close") -> pd.Series:
    """Menghitung Exponential Moving Average."""
    return df[column].ewm(span=period, adjust=False).mean()


def calculate_rsi(df: pd.DataFrame, period: int = 14, column: str = "close") -> pd.Series:
    """Menghitung Relative Strength Index (metode Wilder)."""
    delta = df[column].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    # Saat avg_loss = 0 (harga naik terus), RSI harus 100
    rsi = rsi.where(avg_loss != 0, 100.0)
    return rsi


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Menghitung Average True Range (metode Wilder)."""
    high_low = df["high"] - df["low"]
    high_prev_close = (df["high"] - df["close"].shift(1)).abs()
    low_prev_close = (df["low"] - df["close"].shift(1)).abs()

    true_range = pd.concat([high_low, high_prev_close, low_prev_close], axis=1).max(axis=1)
    atr = true_range.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    return atr


def add_all_indicators(df: pd.DataFrame, ema_fast: int, ema_slow: int,
                        rsi_period: int, atr_period: int) -> pd.DataFrame:
    """Menambahkan semua indikator sekaligus ke DataFrame, mengembalikan copy baru."""
    result = df.copy()
    result[f"ema_{ema_fast}"] = calculate_ema(result, ema_fast)
    result[f"ema_{ema_slow}"] = calculate_ema(result, ema_slow)
    result["rsi"] = calculate_rsi(result, rsi_period)
    result["atr"] = calculate_atr(result, atr_period)
    return result
