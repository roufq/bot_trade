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
) -> Optional[OrderPlan]:
    """Membangun rencana order lengkap: lot, SL, TP, sesuai batasan broker."""
    lot_size, sl_distance = calculate_lot_size(
        equity, atr_value, contract_size, tick_value, tick_size,
        risk_percent,
    )

    market_multiplier = 1.0 + max(0.0, min(0.25, market_score - 0.5))
    tp_distance = atr_value * config.TP_ATR_MULTIPLIER * market_multiplier

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
