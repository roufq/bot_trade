"""
risk_manager.py
Menghitung ukuran lot berdasarkan % risiko equity, menentukan SL/TP dari ATR,
dan memantau drawdown harian untuk menghentikan bot jika limit tersentuh.
"""

from dataclasses import dataclass
import math
from typing import Optional

import config


@dataclass
class OrderPlan:
    lot_size: float
    sl_price: float
    tp_price: float
    sl_distance: float
    tp_distance: float
    risk_amount: float


def round_to_tick(price: float, tick_size: float) -> float:
    """
    Membulatkan harga ke kelipatan tick_size terdekat -- presisi otomatis
    menyesuaikan instrumen (2 desimal untuk XAUUSD, 5 desimal untuk EURUSD,
    dst), BUKAN dibulatkan paksa ke jumlah desimal tetap.
    """
    if tick_size <= 0:
        return price
    return round(round(price / tick_size) * tick_size, 8)


def calculate_lot_size(
    equity: float,
    atr_value: float,
    contract_size: float,
    tick_value: float,
    tick_size: float,
    risk_percent: float,
) -> tuple[float, float]:
    """
    Menghitung ukuran lot berdasarkan % risiko equity dan jarak SL (ATR).

    Parameters
    ----------
    equity : saldo equity akun saat ini
    atr_value : nilai ATR terakhir (dalam satuan harga, misal $ untuk XAUUSD)
    contract_size : ukuran kontrak per 1 lot (dari symbol info MT5)
    tick_value : nilai uang per tick (dari symbol info MT5)
    tick_size : ukuran minimum pergerakan harga (dari symbol info MT5)
    risk_percent : persentase equity yang dirisikokan per trade

    Returns
    -------
    (lot_size, sl_distance_in_price)
    """
    sl_distance = atr_value * config.SL_ATR_MULTIPLIER
    risk_amount = equity * (risk_percent / 100.0)

    # Nilai kerugian per 1 lot jika harga bergerak sejauh sl_distance
    value_per_price_unit = tick_value / tick_size  # nilai uang per 1 unit harga, per lot
    loss_per_lot = sl_distance * value_per_price_unit

    if loss_per_lot <= 0:
        return 0.0, sl_distance

    lot_size = risk_amount / loss_per_lot
    return lot_size, sl_distance


def structural_stop_price(
    candles,
    signal: str,
    entry_price: float,
    atr_value: float,
    spread_price: float,
    tick_size: float,
) -> tuple[float | None, str]:
    """Tempatkan stop di luar swing terkonfirmasi, dengan buffer noise pasar."""
    if not config.STRUCTURAL_STOP_ENABLED:
        return None, "structural stop nonaktif"
    if candles is None or len(candles) < 7 or atr_value <= 0:
        return None, "candle/swing tidak cukup"
    frame = candles.sort_values("time").tail(config.STRUCTURAL_STOP_LOOKBACK_BARS + 3).copy()
    # Candle terakhir dapat masih berjalan. Swing harus memiliki candle di kanan
    # agar level yang dipakai benar-benar sudah terkonfirmasi.
    frame = frame.iloc[:-1].reset_index(drop=True)
    if len(frame) < 5:
        return None, "candle tertutup tidak cukup"
    lows = frame["low"].astype(float)
    highs = frame["high"].astype(float)
    swing_lows = [i for i in range(2, len(frame) - 2) if lows.iloc[i] <= lows.iloc[i-2:i].min() and lows.iloc[i] < lows.iloc[i+1:i+3].min()]
    swing_highs = [i for i in range(2, len(frame) - 2) if highs.iloc[i] >= highs.iloc[i-2:i].max() and highs.iloc[i] > highs.iloc[i+1:i+3].max()]
    buffer_distance = max(
        atr_value * config.STRUCTURAL_STOP_BUFFER_ATR,
        max(0.0, spread_price) * config.STRUCTURAL_STOP_SPREAD_MULTIPLIER,
        max(0.0, tick_size),
    )
    minimum_distance = atr_value * config.SL_ATR_MULTIPLIER
    if signal == "buy":
        if not swing_lows:
            return None, "swing low terkonfirmasi tidak ditemukan"
        structure = float(lows.iloc[swing_lows[-1]])
        candidate = structure - buffer_distance
        stop = min(candidate, entry_price - minimum_distance)
        if stop >= entry_price:
            return None, "swing low tidak berada di bawah entry"
    elif signal == "sell":
        if not swing_highs:
            return None, "swing high terkonfirmasi tidak ditemukan"
        structure = float(highs.iloc[swing_highs[-1]])
        candidate = structure + buffer_distance
        stop = max(candidate, entry_price + minimum_distance)
        if stop <= entry_price:
            return None, "swing high tidak berada di atas entry"
    else:
        return None, "arah sinyal tidak valid"
    return round_to_tick(stop, tick_size), f"swing={structure:.5f}, buffer={buffer_distance:.5f}"


def build_order_plan(
    signal: str,
    entry_price: float,
    atr_value: float,
    equity: float,
    contract_size: float,
    tick_value: float,
    tick_size: float,
    volume_min: float,
    volume_max: float,
    volume_step: float,
    risk_percent: float,
    market_score: float = 0.0,
    structural_sl_price: float | None = None,
) -> Optional[OrderPlan]:
    """Membangun rencana order lengkap: lot, SL, TP, sesuai batasan broker."""
    lot_size, sl_distance = calculate_lot_size(
        equity, atr_value, contract_size, tick_value, tick_size,
        risk_percent,
    )

    market_multiplier = 1.0 + max(0.0, min(0.25, market_score - 0.5))
    tp_distance = atr_value * config.TP_ATR_MULTIPLIER * market_multiplier

    if structural_sl_price is not None:
        structural_distance = abs(entry_price - structural_sl_price)
        structurally_valid = (
            signal == "buy" and structural_sl_price < entry_price
            or signal == "sell" and structural_sl_price > entry_price
        )
        if not structurally_valid or structural_distance <= 0:
            return None
        if structural_distance > atr_value * config.STRUCTURAL_STOP_MAX_ATR:
            return None
        if tp_distance / structural_distance < config.STRUCTURAL_STOP_MIN_REWARD_RISK:
            return None
        sl_distance = structural_distance
        risk_amount_target = equity * (risk_percent / 100.0)
        lot_size = risk_amount_target / (sl_distance * (tick_value / tick_size))

    if volume_step <= 0 or volume_min <= 0 or volume_max < volume_min:
        return None

    # Selalu bulatkan ke bawah agar risiko aktual tidak melewati target.
    lot_size = math.floor((lot_size + 1e-12) / volume_step) * volume_step
    if lot_size < volume_min:
        min_lot_risk_amount = sl_distance * (tick_value / tick_size) * volume_min
        min_lot_risk_percent = (min_lot_risk_amount / equity) * 100.0 if equity > 0 else float("inf")
        if min_lot_risk_percent > config.MAX_ACTUAL_RISK_PERCENT_PER_TRADE:
            return None
        lot_size = volume_min
    lot_size = min(lot_size, volume_max)

    if lot_size <= 0:
        return None

    if signal == "buy":
        sl_price = entry_price - sl_distance
        tp_price = entry_price + tp_distance
    elif signal == "sell":
        sl_price = entry_price + sl_distance
        tp_price = entry_price - tp_distance
    else:
        return None

    value_per_price_unit = tick_value / tick_size
    risk_amount = sl_distance * value_per_price_unit * lot_size

    return OrderPlan(
        lot_size=lot_size,
        sl_price=round_to_tick(sl_price, tick_size),
        tp_price=round_to_tick(tp_price, tick_size),
        sl_distance=sl_distance,
        tp_distance=tp_distance,
        risk_amount=risk_amount,
    )


def check_daily_drawdown(equity_start_of_day: float, equity_now: float) -> tuple[bool, float]:
    """
    Mengecek apakah drawdown harian sudah melewati limit.

    Returns
    -------
    (limit_tersentuh: bool, drawdown_percent: float)
    """
    if equity_start_of_day <= 0:
        return False, 0.0

    drawdown_percent = ((equity_start_of_day - equity_now) / equity_start_of_day) * 100.0
    limit_hit = drawdown_percent >= config.MAX_DAILY_DRAWDOWN_PERCENT
    return limit_hit, drawdown_percent


def can_open_new_position(current_open_positions: int) -> bool:
    """Cek apakah masih ada slot untuk posisi baru (batasan jumlah, kasar)."""
    return current_open_positions < config.MAX_OPEN_POSITIONS


def can_open_direction(open_positions: list, signal: str, entry_price: float, atr: float) -> tuple[bool, str]:
    """Batasi hedge berlawanan, posisi searah, jarak, dan averaging saat rugi."""
    desired_type = 0 if signal == "buy" else 1
    same_direction = [pos for pos in open_positions if int(pos.type) == desired_type]
    opposite = [pos for pos in open_positions if int(pos.type) != desired_type]
    if opposite and not config.ALLOW_OPPOSITE_HEDGE:
        return False, (
            f"posisi berlawanan masih terbuka ({len(opposite)} posisi); "
            f"hedge {signal} dinonaktifkan"
        )
    if len(same_direction) >= config.MAX_POSITIONS_PER_DIRECTION:
        return False, f"posisi {signal} sudah {len(same_direction)}/{config.MAX_POSITIONS_PER_DIRECTION}"
    if not config.ALLOW_ADD_TO_LOSING_POSITION and any(float(getattr(pos, "profit", 0.0)) < 0 for pos in same_direction):
        return False, f"posisi {signal} sebelumnya masih floating loss"
    minimum_distance = max(0.0, atr * config.MIN_ENTRY_DISTANCE_ATR)
    if any(abs(entry_price - float(pos.price_open)) < minimum_distance for pos in same_direction):
        return False, f"jarak entry {signal} kurang dari {config.MIN_ENTRY_DISTANCE_ATR:.2f} ATR"
    return True, ""


def calculate_total_open_risk_percent(open_positions: list, equity: float,
                                       tick_value: float, tick_size: float) -> float:
    """
    Menghitung TOTAL risiko (dalam %) dari semua posisi yang sedang terbuka,
    berdasarkan jarak masing-masing ke SL-nya. Ini batasan yang lebih presisi
    dibanding sekadar menghitung jumlah posisi -- karena jumlah posisi yang
    sama bisa punya total risiko sangat berbeda tergantung SL masing-masing.
    """
    if equity <= 0 or not open_positions:
        return 0.0

    value_per_unit = tick_value / tick_size
    total_risk_amount = 0.0
    for pos in open_positions:
        sl_distance = abs(pos.price_open - pos.sl) if pos.sl else 0.0
        total_risk_amount += sl_distance * value_per_unit * pos.volume

    return (total_risk_amount / equity) * 100.0


def can_open_within_risk_budget(open_positions: list, equity: float,
                                 tick_value: float, tick_size: float,
                                 next_risk_percent: float) -> tuple[bool, float]:
    """
    Cek apakah menambah 1 posisi baru dengan risiko adaptif masih aman dalam
    batas MAX_TOTAL_OPEN_RISK_PERCENT.

    Returns
    -------
    (boleh_buka: bool, total_risiko_terbuka_sekarang_persen: float)
    """
    current_risk_pct = calculate_total_open_risk_percent(open_positions, equity, tick_value, tick_size)
    projected_risk_pct = current_risk_pct + next_risk_percent
    return projected_risk_pct <= config.MAX_TOTAL_OPEN_RISK_PERCENT, current_risk_pct
