"""
diagnose_trade_disabled_v2.py
Memaksa symbol_select dulu (memastikan simbol aktif dipantau), lalu cek ulang
trade_mode -- kadang trade_mode baru valid setelah simbol benar-benar
disubscribe di sesi ini.
"""

import time
import MetaTrader5 as mt5
import config

mt5.initialize()

print(f"Memaksa subscribe simbol {config.SYMBOL}...")
selected = mt5.symbol_select(config.SYMBOL, True)
print("symbol_select berhasil:", selected)

time.sleep(2)  # beri jeda supaya data simbol sempat termuat penuh

sym = mt5.symbol_info(config.SYMBOL)
print("\n=== INFO SIMBOL (setelah subscribe) ===")
print("visible        :", sym.visible if sym else None)
print("trade_mode     :", sym.trade_mode if sym else None, "(0=DISABLED, 1=LONGONLY, 2=SHORTONLY, 3=CLOSEONLY, 4=FULL)")
print("trade_calc_mode:", sym.trade_calc_mode if sym else None)
print("session_deals  :", sym.session_deals if sym else None, "(0 berarti sesi trading sedang tidak aktif)")

tick = mt5.symbol_info_tick(config.SYMBOL)
print("\n=== TICK TERKINI ===")
print("bid/ask        :", (tick.bid, tick.ask) if tick else None)
print("waktu tick     :", tick.time if tick else None)

print("\n=== WAKTU SERVER BROKER ===")
print("Waktu server (dari tick) menunjukkan kapan data terakhir update.")
print("Bandingkan dengan waktu di pojok kanan bawah MT5 desktop Anda.")

mt5.shutdown()
