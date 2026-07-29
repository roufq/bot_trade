"""Bangun dataset sinyal historis dari candle tertutup tanpa look-ahead fitur."""

import csv
from pathlib import Path

import pandas as pd

import ai_trader
import config
import mt5_connector
import strategy


def _outcome(future: pd.DataFrame, signal: str, entry: float, atr: float) -> tuple[float, object] | None:
    sl_distance = atr * config.SL_ATR_MULTIPLIER
    tp_distance = atr * config.TP_ATR_MULTIPLIER
    sl = entry - sl_distance if signal == "buy" else entry + sl_distance
    tp = entry + tp_distance if signal == "buy" else entry - tp_distance
    for candle in future.itertuples():
        sl_hit = float(candle.low) <= sl if signal == "buy" else float(candle.high) >= sl
        tp_hit = float(candle.high) >= tp if signal == "buy" else float(candle.low) <= tp
        # Urutan tick tidak diketahui; asumsi loss adalah pilihan konservatif.
        if sl_hit or tp_hit:
            result_r = -1.0 if sl_hit else config.TP_ATR_MULTIPLIER / config.SL_ATR_MULTIPLIER
            return result_r, candle.time
    return None


def generate(max_m1_bars: int | None = None) -> dict:
    """Replay strategi A-L dan tulis hanya setup yang outcome-nya sudah diketahui."""
    limit = max_m1_bars or config.AI_REPLAY_MAX_M1_BARS
    if not mt5_connector.connect():
        return {"success": False, "reason": "koneksi MT5 gagal", "rows": 0}
    try:
        m1 = mt5_connector.get_rates(config.SYMBOL, "M1", count=limit, include_spread=True)
        h1 = mt5_connector.get_rates(config.SYMBOL, config.FVG_TF_CONTEXT, count=min(3000, limit))
        m15 = mt5_connector.get_rates(config.SYMBOL, config.FVG_TF_ZONE, count=min(12000, limit))
        symbol_info = mt5_connector.get_symbol_info(config.SYMBOL)
    finally:
        mt5_connector.disconnect()
    if any(frame is None or frame.empty for frame in (m1, h1, m15)) or symbol_info is None:
        return {"success": False, "reason": "candle/symbol info tidak lengkap", "rows": 0}

    m1 = m1.sort_values("time").reset_index(drop=True)
    h1 = h1.sort_values("time").reset_index(drop=True)
    m15 = m15.sort_values("time").reset_index(drop=True)
    point = float(symbol_info.get("point", symbol_info["trade_tick_size"]))
    horizon = config.AI_REPLAY_OUTCOME_HORIZON_BARS
    warmup = max(100, config.EMA_TREND_SLOW + config.ATR_PERIOD + 5)
    last_signal_index: dict[tuple[str, str], int] = {}
    rows: list[dict] = []

    h1_times = h1["time"].to_numpy(dtype="datetime64[ns]")
    m15_times = m15["time"].to_numpy(dtype="datetime64[ns]")
    scan_step = max(1, config.AI_REPLAY_SCAN_STEP_BARS)
    for index in range(warmup, len(m1) - horizon, scan_step):
        signal_time = m1.iloc[index]["time"]
        entry_history = m1.iloc[max(0, index - 299):index + 1]
        h1_end = int(h1_times.searchsorted(signal_time.to_datetime64(), side="right"))
        m15_end = int(m15_times.searchsorted(signal_time.to_datetime64(), side="right"))
        h1_history = h1.iloc[max(0, h1_end - 300):h1_end]
        m15_history = m15.iloc[max(0, m15_end - 300):m15_end]
        if len(h1_history) < 20 or len(m15_history) < 20:
            continue
        result = strategy.evaluate_hybrid(
            entry_history, entry_history, h1_history, m15_history, entry_history.tail(100),
        )
        if result.signal == "none" or not result.atr_value:
            continue
        key = (result.strategy_source, result.signal)
        if index - last_signal_index.get(key, -10000) < config.AI_REPLAY_MIN_SIGNAL_SPACING_BARS:
            continue
        last_signal_index[key] = index
        spread_points = float(m1.iloc[index].get("spread", 0.0) or 0.0)
        close = float(m1.iloc[index]["close"])
        entry = close + spread_points * point if result.signal == "buy" else close
        resolved = _outcome(m1.iloc[index + 1:index + 1 + horizon], result.signal, entry, float(result.atr_value))
        if resolved is None:
            continue
        result_r, resolved_time = resolved
        features = ai_trader.extract_features(
            entry_history, entry_history, result, spread_points=spread_points,
        )
        rows.append({
            "signal_time": signal_time, "resolved_time": resolved_time,
            "signal": result.signal, "strategy_source": result.strategy_source,
            "result_r": result_r, **features,
        })

    path = Path(config.HISTORICAL_SIGNAL_DATASET_FILE)
    fields = ["signal_time", "resolved_time", "signal", "strategy_source", "result_r", *ai_trader.FEATURE_COLUMNS]
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)
    return {
        "success": True, "reason": "ok", "rows": len(rows),
        "scan_step_bars": scan_step,
        "start": str(m1.iloc[0]["time"]), "end": str(m1.iloc[-1]["time"]),
        "path": str(path),
    }


if __name__ == "__main__":
    print(generate())
