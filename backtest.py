"""
backtest.py
Menjalankan strategi terhadap data historis MT5 untuk mendapatkan estimasi
performa (win rate, profit factor, drawdown) SEBELUM dipercaya untuk live/demo.

PENTING -- keterbatasan backtest ini (baca sebelum percaya hasilnya):
- Spread & komisi disederhanakan jadi biaya tetap per trade (dari spread SAAT
  INI), bukan spread historis riil yang berubah-ubah dari waktu ke waktu.
- Kalau SL dan TP sama-sama tersentuh dalam 1 candle yang sama, backtest
  mengasumsikan SL kena duluan (asumsi konservatif -- bisa saja di kenyataan
  TP yang kena duluan, sehingga hasil asli sedikit lebih baik dari ini).
- Jam trading pakai waktu SERVER MT5 broker, BUKAN otomatis WIB -- cek dulu
  apakah TRADING_HOUR_START/END di config.py sudah sesuai zona waktu server
  (lihat jam di pojok kanan bawah MT5 dan bandingkan dengan jam WIB Anda).
- MT5 punya batas jumlah candle historis yang bisa diambil sekaligus,
  tergantung pengaturan terminal & broker -- cek output "rentang data"
  di bawah untuk tahu berapa bulan riil yang benar-benar didapat.
- Hasil masa lalu TIDAK menjamin hasil masa depan.

Jalankan dengan: python backtest.py
"""

import numpy as np
import pandas as pd

import config
import mt5_connector
import indicators
import risk_manager
import strategy

BACKTEST_MONTHS = 6          # berapa bulan ke belakang data yang diminta
INITIAL_EQUITY = 100.0       # modal awal simulasi -- sesuaikan sesuai rencana Anda

# Durasi tiap timeframe dalam menit -- dipakai untuk menghitung offset
# "candle baru tersedia setelah X menit" dan jumlah candle yang diminta,
# supaya otomatis benar untuk timeframe apapun (M1, M15, H1, dst),
# bukan hardcode asumsi H1 seperti sebelumnya.
TIMEFRAME_MINUTES = {
    "M1": 1, "M5": 5, "M15": 15, "M30": 30, "H1": 60, "H4": 240, "D1": 1440,
}


MAX_BARS_PER_REQUEST = 20000  # batas aman -- MT5 sering menolak permintaan candle yang terlalu banyak sekaligus


def fetch_backtest_data():
    bars_per_day_trend = (24 * 60) // TIMEFRAME_MINUTES[config.TF_TREND]
    bars_per_day_entry = (24 * 60) // TIMEFRAME_MINUTES[config.TF_ENTRY]
    count_trend = min(BACKTEST_MONTHS * 30 * bars_per_day_trend, MAX_BARS_PER_REQUEST)
    count_entry = min(BACKTEST_MONTHS * 30 * bars_per_day_entry, MAX_BARS_PER_REQUEST)

    requested_trend = BACKTEST_MONTHS * 30 * bars_per_day_trend
    requested_entry = BACKTEST_MONTHS * 30 * bars_per_day_entry
    if requested_trend > MAX_BARS_PER_REQUEST:
        actual_days = count_trend / bars_per_day_trend
        print(f"Catatan: data {config.TF_TREND} dibatasi ke {count_trend} candle "
              f"(~{actual_days:.1f} hari) -- {BACKTEST_MONTHS} bulan penuh terlalu banyak untuk 1 permintaan.")
    if requested_entry > MAX_BARS_PER_REQUEST:
        actual_days = count_entry / bars_per_day_entry
        print(f"Catatan: data {config.TF_ENTRY} dibatasi ke {count_entry} candle "
              f"(~{actual_days:.1f} hari) -- {BACKTEST_MONTHS} bulan penuh terlalu banyak untuk 1 permintaan.")

    df_h1 = mt5_connector.get_rates(config.SYMBOL, config.TF_TREND, count=count_trend)
    df_m15 = mt5_connector.get_rates(config.SYMBOL, config.TF_ENTRY, count=count_entry)
    fvg_h1_count = min(BACKTEST_MONTHS * 30 * 24, MAX_BARS_PER_REQUEST)
    fvg_m15_count = min(BACKTEST_MONTHS * 30 * 24 * 4, MAX_BARS_PER_REQUEST)
    df_fvg_h1 = mt5_connector.get_rates(config.SYMBOL, config.FVG_TF_CONTEXT, count=fvg_h1_count)
    df_fvg_m15 = mt5_connector.get_rates(config.SYMBOL, config.FVG_TF_ZONE, count=fvg_m15_count)
    df_m1 = (
        df_m15 if config.TF_ENTRY == config.FVG_TF_TRIGGER
        else mt5_connector.get_rates(config.SYMBOL, config.FVG_TF_TRIGGER, count=count_entry)
    )
    return df_h1, df_m15, df_fvg_h1, df_fvg_m15, df_m1


def prepare_h1_bias(df_h1: pd.DataFrame) -> pd.DataFrame:
    df = df_h1.copy()
    fast_col = f"ema_{config.EMA_TREND_FAST}"
    slow_col = f"ema_{config.EMA_TREND_SLOW}"
    df[fast_col] = indicators.calculate_ema(df, config.EMA_TREND_FAST)
    df[slow_col] = indicators.calculate_ema(df, config.EMA_TREND_SLOW)

    conditions = [
        (df["close"] > df[fast_col]) & (df[fast_col] > df[slow_col]),
        (df["close"] < df[fast_col]) & (df[fast_col] < df[slow_col]),
    ]
    df["bias"] = np.select(conditions, ["buy", "sell"], default="none")

    # Bias dari candle TF_TREND baru "tersedia" setelah candle itu resmi
    # tertutup -- offset otomatis mengikuti timeframe yang dipakai (misal
    # 1 menit untuk M1, bukan hardcode 1 jam), supaya tidak memakai info
    # yang seharusnya belum tersedia pada saat itu.
    offset_minutes = TIMEFRAME_MINUTES[config.TF_TREND]
    df["available_time"] = (df["time"] + pd.Timedelta(minutes=offset_minutes)).astype("datetime64[ns]")
    return df[["available_time", "bias"]]


def prepare_m15_signals(df_m15: pd.DataFrame) -> pd.DataFrame:
    df = df_m15.copy()
    fast_col = f"ema_{config.EMA_ENTRY_FAST}"
    slow_col = f"ema_{config.EMA_ENTRY_SLOW}"
    df[fast_col] = indicators.calculate_ema(df, config.EMA_ENTRY_FAST)
    df[slow_col] = indicators.calculate_ema(df, config.EMA_ENTRY_SLOW)
    df["rsi"] = indicators.calculate_rsi(df, config.RSI_PERIOD)
    df["atr"] = indicators.calculate_atr(df, config.ATR_PERIOD)

    prev_fast = df[fast_col].shift(1)
    prev_slow = df[slow_col].shift(1)
    df["crossed_up"] = (prev_fast <= prev_slow) & (df[fast_col] > df[slow_col])
    df["crossed_down"] = (prev_fast >= prev_slow) & (df[fast_col] < df[slow_col])
    df["time"] = df["time"].astype("datetime64[ns]")
    return df


def estimate_spread_cost(symbol_info: dict) -> float:
    """Perkiraan biaya spread per trade di lot minimum, pakai spread SAAT INI sebagai proxy."""
    tick = mt5_connector.mt5.symbol_info_tick(config.SYMBOL)
    if tick is None:
        return 0.0
    spread_price = tick.ask - tick.bid
    value_per_unit = symbol_info["trade_tick_value"] / symbol_info["trade_tick_size"]
    return spread_price * value_per_unit * symbol_info["volume_min"]


def run_backtest():
    if not mt5_connector.connect():
        print("Koneksi gagal.")
        return

    print(f"Mengambil data historis {config.SYMBOL} (target {BACKTEST_MONTHS} bulan)...")
    df_h1, df_m15, df_fvg_h1, df_fvg_m15, df_m1 = fetch_backtest_data()
    if any(frame is None or len(frame) == 0 for frame in (df_h1, df_m15, df_fvg_h1, df_fvg_m15, df_m1)):
        print("Gagal mengambil data historis.")
        mt5_connector.disconnect()
        return

    print(f"Rentang data {config.TF_TREND} : {df_h1['time'].iloc[0]} s/d {df_h1['time'].iloc[-1]} ({len(df_h1)} candle)")
    print(f"Rentang data {config.TF_ENTRY} : {df_m15['time'].iloc[0]} s/d {df_m15['time'].iloc[-1]} ({len(df_m15)} candle)")

    symbol_info = mt5_connector.get_symbol_info(config.SYMBOL)
    spread_cost = estimate_spread_cost(symbol_info)
    print(f"Asumsi biaya spread per trade (lot minimum): ${spread_cost:.4f} (perkiraan dari spread saat ini)\n")

    df_h1 = df_h1.sort_values("time").reset_index(drop=True)
    df_m15 = df_m15.sort_values("time").reset_index(drop=True)
    df_fvg_h1 = df_fvg_h1.sort_values("time").reset_index(drop=True)
    df_fvg_m15 = df_fvg_m15.sort_values("time").reset_index(drop=True)
    df_m1 = df_m1.sort_values("time").reset_index(drop=True)
    equity = INITIAL_EQUITY
    equity_start_of_day = equity
    current_day = None
    daily_stopped = False
    positions = []
    trades = []
    equity_curve = []
    warmup = max(config.EMA_TREND_SLOW, config.EMA_ENTRY_SLOW, config.ATR_PERIOD) + 5

    # Candle indeks i adalah candle eksekusi. Sinyal hanya melihat candle < i,
    # sama seperti live yang memakai closed_only=True.
    for i in range(warmup, len(df_m1)):
        row = df_m1.iloc[i]
        bar_day = row.time.date()
        if bar_day != current_day:
            current_day = bar_day
            equity_start_of_day = equity
            daily_stopped = False

        remaining = []
        for position in positions:
            if position["direction"] == "buy":
                hit_sl = float(row.low) <= position["sl"]
                hit_tp = float(row.high) >= position["tp"]
            else:
                hit_sl = float(row.high) >= position["sl"]
                hit_tp = float(row.low) <= position["tp"]

            if hit_sl or hit_tp:
                exit_price = position["sl"] if hit_sl else position["tp"]
                if position["direction"] == "buy":
                    price_diff = exit_price - position["entry_price"]
                else:
                    price_diff = position["entry_price"] - exit_price

                value_per_unit = symbol_info["trade_tick_value"] / symbol_info["trade_tick_size"]
                gross_profit = price_diff * value_per_unit * position["lot"]
                # Spread sudah dimasukkan pada harga entry buy. Untuk sell,
                # biaya spread direalisasikan pada exit ask sebagai proxy.
                net_profit = gross_profit - (spread_cost if position["direction"] == "sell" else 0.0)
                equity += net_profit

                trades.append({
                    "entry_time": position["entry_time"],
                    "exit_time": row.time,
                    "direction": position["direction"],
                    "lot": position["lot"],
                    "entry_price": position["entry_price"],
                    "exit_price": exit_price,
                    "result": "TP" if hit_tp and not hit_sl else "SL",
                    "profit": net_profit,
                    "equity_after": equity,
                    "strategy_source": position.get("strategy_source", "UNKNOWN"),
                })
            else:
                remaining.append(position)
        positions = remaining

        equity_curve.append({"time": row.time, "equity": equity})

        if daily_stopped:
            continue
        limit_hit, _ = risk_manager.check_daily_drawdown(equity_start_of_day, equity)
        if limit_hit:
            daily_stopped = True
            continue

        if not (config.TRADING_HOUR_START <= row.time.hour < config.TRADING_HOUR_END):
            continue

        if len(positions) >= config.MAX_OPEN_POSITIONS:
            continue
        entry_history = df_m15[df_m15["time"] < row.time].tail(100)
        trend_history = df_h1[df_h1["time"] < row.time].tail(300)
        fvg_h1_history = df_fvg_h1[df_fvg_h1["time"] < row.time].tail(300)
        fvg_m15_history = df_fvg_m15[df_fvg_m15["time"] < row.time].tail(300)
        m1_history = df_m1.iloc[:i].tail(100)
        if len(entry_history) < warmup or len(trend_history) < warmup or len(m1_history) < warmup:
            continue
        signal_result = strategy.evaluate_hybrid(
            trend_history, entry_history, fvg_h1_history, fvg_m15_history, m1_history,
        )
        if signal_result.signal == "none" or not signal_result.atr_value:
            continue
        signal = signal_result.signal
        # OHLC MT5 umumnya berbasis bid; buy membayar spread pada entry.
        spread_price = spread_cost / (
            (symbol_info["trade_tick_value"] / symbol_info["trade_tick_size"])
            * symbol_info["volume_min"]
        ) if spread_cost > 0 else 0.0
        entry_price = float(row.open) + spread_price if signal == "buy" else float(row.open)
        risk_percent = config.RISK_PERCENT_PER_TRADE
        risk_percent *= strategy.risk_multiplier_for(signal_result.strategy_source)
        order_plan = risk_manager.build_order_plan(
            signal=signal,
            entry_price=entry_price,
            atr_value=signal_result.atr_value,
            equity=equity,
            contract_size=symbol_info["trade_contract_size"],
            tick_value=symbol_info["trade_tick_value"],
            tick_size=symbol_info["trade_tick_size"],
            volume_min=symbol_info["volume_min"],
            volume_max=symbol_info["volume_max"],
            volume_step=symbol_info["volume_step"],
            risk_percent=risk_percent,
        )
        if order_plan is None:
            continue

        positions.append({
            "direction": signal,
            "entry_price": entry_price,
            "sl": order_plan.sl_price,
            "tp": order_plan.tp_price,
            "lot": order_plan.lot_size,
            "entry_time": row.time,
            "strategy_source": signal_result.strategy_source,
        })

    mt5_connector.disconnect()

    trades_df = pd.DataFrame(trades)
    trades_df.to_csv("backtest_trades.csv", index=False)

    equity_df = pd.DataFrame(equity_curve)
    equity_df.to_csv("backtest_equity_curve.csv", index=False)

    print_summary(trades_df, equity_df)


def print_summary(trades_df: pd.DataFrame, equity_df: pd.DataFrame) -> None:
    print("=" * 50)
    print(f"HASIL BACKTEST -- {config.SYMBOL}")
    print("=" * 50)

    if trades_df.empty:
        print("Tidak ada trade sama sekali dalam periode ini.")
        print("Ini bisa berarti strategi sangat selektif untuk kondisi pasar kemarin,")
        print("atau filter terlalu ketat. Coba perpanjang BACKTEST_MONTHS di file ini.")
        return

    total_trades = len(trades_df)
    wins = trades_df[trades_df["profit"] > 0]
    losses = trades_df[trades_df["profit"] <= 0]
    win_rate = len(wins) / total_trades * 100

    gross_profit = wins["profit"].sum()
    gross_loss = abs(losses["profit"].sum())
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float("inf")

    net_profit = trades_df["profit"].sum()
    final_equity = INITIAL_EQUITY + net_profit

    running_max = equity_df["equity"].cummax()
    drawdown = (running_max - equity_df["equity"]) / running_max * 100
    max_drawdown = drawdown.max()

    print(f"Total trade            : {total_trades}")
    print(f"Win rate                : {win_rate:.1f}%  ({len(wins)} menang, {len(losses)} kalah)")
    print(f"Profit factor           : {profit_factor:.2f}  (di atas 1.0 = profit > rugi total)")
    print(f"Net profit              : ${net_profit:.2f}")
    print(f"Equity awal -> akhir    : ${INITIAL_EQUITY:.2f} -> ${final_equity:.2f}")
    print(f"Max drawdown            : {max_drawdown:.2f}%")
    print(f"Rata-rata trade/bulan   : {total_trades / BACKTEST_MONTHS:.1f}")
    if "strategy_source" in trades_df.columns:
        print("\nPerforma per sumber strategi:")
        for source, group in trades_df.groupby("strategy_source"):
            source_wins = group[group["profit"] > 0]
            source_losses = group[group["profit"] <= 0]
            source_gross_loss = abs(source_losses["profit"].sum())
            source_pf = (
                source_wins["profit"].sum() / source_gross_loss
                if source_gross_loss > 0 else float("inf")
            )
            print(
                f"  {source}: {len(group)} trade, win rate={len(source_wins) / len(group):.1%}, "
                f"PF={source_pf:.2f}, net=${group['profit'].sum():+.2f}"
            )
    print()
    print("Detail lengkap disimpan di: backtest_trades.csv, backtest_equity_curve.csv")
    print()
    print("PENGINGAT: ini hasil dari data MASA LALU, bukan jaminan hasil masa depan.")
    print("Baca komentar keterbatasan di awal file backtest.py sebelum mengambil keputusan.")


if __name__ == "__main__":
    run_backtest()
