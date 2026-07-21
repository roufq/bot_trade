"""Break-even dan trailing stop yang hanya menggeser SL ke arah lebih aman."""

import config
import mt5_connector
import risk_manager


def manage(open_positions: list, atr: float, ask: float, bid: float, symbol_info: dict) -> list[str]:
    if not open_positions or atr <= 0:
        return []
    point = float(symbol_info.get("point", symbol_info.get("trade_tick_size", 0.0)) or 0.0)
    tick_size = float(symbol_info.get("trade_tick_size", point) or point)
    events = []
    for pos in open_positions:
        is_buy = int(pos.type) == 0
        current = bid if is_buy else ask
        favorable = current - pos.price_open if is_buy else pos.price_open - current
        proposed = float(pos.sl or 0.0)

        if config.BREAK_EVEN_ENABLED and favorable >= atr * config.BREAK_EVEN_TRIGGER_ATR:
            offset = point * config.BREAK_EVEN_OFFSET_POINTS
            break_even = pos.price_open + offset if is_buy else pos.price_open - offset
            if proposed == 0 or (is_buy and break_even > proposed) or (not is_buy and break_even < proposed):
                proposed = break_even

        if config.TRAILING_STOP_ENABLED and favorable >= atr * config.TRAILING_TRIGGER_ATR:
            trailing = current - atr * config.TRAILING_DISTANCE_ATR if is_buy else current + atr * config.TRAILING_DISTANCE_ATR
            if proposed == 0 or (is_buy and trailing > proposed) or (not is_buy and trailing < proposed):
                proposed = trailing

        proposed = risk_manager.round_to_tick(proposed, tick_size)
        if proposed <= 0 or proposed == float(pos.sl or 0.0):
            continue
        # Jangan pernah melewati harga pasar atau memperburuk SL.
        if (is_buy and (proposed >= bid or (pos.sl and proposed <= pos.sl))) or (
            not is_buy and (proposed <= ask or (pos.sl and proposed >= pos.sl))
        ):
            continue
        result = mt5_connector.modify_position_sltp(pos.ticket, pos.symbol, proposed, pos.tp)
        if result["success"]:
            events.append(f"ticket={pos.ticket}, sl={proposed}")
        else:
            events.append(f"ticket={pos.ticket}, gagal={result['error']}")
    return events
