"""
check_min_capital.py
Menghitung modal minimum yang dibutuhkan supaya risk management (1% per trade)
tetap berfungsi sesuai desain, mengingat ada batasan lot minimum dari broker.

Jalankan dengan: python check_min_capital.py
"""

import mt5_connector
import indicators
import config


def main():
    if not mt5_connector.connect():
        print("Koneksi gagal.")
        return

    df_m15 = mt5_connector.get_rates(config.SYMBOL, config.TF_ENTRY, count=100)
    if df_m15 is None:
        print("Gagal ambil data M15.")
        mt5_connector.disconnect()
        return

    atr_series = indicators.calculate_atr(df_m15, period=config.ATR_PERIOD)
    current_atr = float(atr_series.iloc[-1])
    sl_distance = current_atr * config.SL_ATR_MULTIPLIER

    symbol_info = mt5_connector.get_symbol_info(config.SYMBOL)
    volume_min = symbol_info["volume_min"]
    tick_value = symbol_info["trade_tick_value"]
    tick_size = symbol_info["trade_tick_size"]

    loss_per_min_lot = sl_distance * (tick_value / tick_size) * volume_min
    equity_min = loss_per_min_lot / (config.RISK_PERCENT_PER_TRADE / 100.0)

    print(f"ATR M15 saat ini      : ${current_atr:.2f}")
    print(f"Jarak SL (1.5x ATR)   : ${sl_distance:.2f}")
    print(f"Lot minimum broker    : {volume_min}")
    print(f"Kerugian jika SL kena (di lot minimum): ${loss_per_min_lot:.2f}")
    print(f"\n=== MODAL MINIMUM AGAR RISIKO TETAP {config.RISK_PERCENT_PER_TRADE}% ===")
    print(f"${equity_min:.2f}")
    print(f"\nCatatan: angka ini berubah-ubah mengikuti ATR saat ini. "
          f"Semakin volatile pasar, semakin besar modal minimum yang dibutuhkan.")

    mt5_connector.disconnect()


if __name__ == "__main__":
    main()
