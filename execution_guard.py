"""Validasi kondisi broker dan margin sebelum market order dikirim."""

import time

import config
import mt5_connector


def validate_market_order(
    symbol: str,
    signal: str,
    lot_size: float,
    entry_price: float,
    sl_price: float,
    tp_price: float,
    symbol_info: dict,
    account: dict,
) -> tuple[bool, str]:
    tick = mt5_connector.get_tick_info(symbol)
    if tick is None:
        return False, "tick broker tidak tersedia"
    tick_age = max(0.0, time.time() - float(tick.get("time", 0.0)))
    if tick_age > config.MAX_TICK_AGE_SECONDS:
        return False, f"harga stale {tick_age:.1f} detik"

    point = float(symbol_info.get("point", symbol_info.get("trade_tick_size", 0.0)) or 0.0)
    stops_level = float(symbol_info.get("trade_stops_level", 0.0) or 0.0) * point
    if stops_level > 0:
        if abs(entry_price - sl_price) < stops_level or abs(tp_price - entry_price) < stops_level:
            return False, f"SL/TP lebih dekat dari minimum broker {stops_level}"

    volume_min = float(symbol_info.get("volume_min", 0.0) or 0.0)
    volume_max = float(symbol_info.get("volume_max", 0.0) or 0.0)
    if not (volume_min <= lot_size <= volume_max):
        return False, f"volume {lot_size} di luar batas broker {volume_min}-{volume_max}"

    margin = mt5_connector.calculate_order_margin(symbol, signal, lot_size, entry_price)
    free_margin = float(account.get("margin_free", 0.0) or 0.0)
    if margin is None:
        return False, "broker gagal menghitung margin order"
    remaining = free_margin - margin
    minimum_remaining = free_margin * (config.MIN_FREE_MARGIN_AFTER_ORDER_PERCENT / 100.0)
    if remaining < minimum_remaining:
        return False, f"free margin setelah order terlalu rendah ({remaining:.2f})"
    return True, f"tick_age={tick_age:.1f}s, margin={margin:.2f}"
