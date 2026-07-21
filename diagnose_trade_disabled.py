"""
diagnose_trade_disabled.py
Mengecek 3 kemungkinan penyebab error retcode 10017 "Trade disabled":
1. Login pakai password Investor (read-only) bukan Master/Trader
2. Simbol dalam mode terbatas (disabled/close-only)
3. Algo Trading belum benar-benar aktif

Jalankan dengan: python diagnose_trade_disabled.py
"""

import MetaTrader5 as mt5
import config

mt5.initialize()

acc = mt5.account_info()
print("=== INFO AKUN ===")
print("trade_allowed  :", acc.trade_allowed if acc else None, "(harus True -- kalau False, Anda login pakai password Investor)")
print("trade_mode     :", acc.trade_mode if acc else None, "(0=demo, 1=contest, 2=real)")

sym = mt5.symbol_info(config.SYMBOL)
print("\n=== INFO SIMBOL ===")
print("trade_mode     :", sym.trade_mode if sym else None, "(0=DISABLED, 1=LONGONLY, 2=SHORTONLY, 3=CLOSEONLY, 4=FULL -- harus 4)")

term = mt5.terminal_info()
print("\n=== INFO TERMINAL ===")
print("trade_allowed  :", term.trade_allowed if term else None, "(harus True -- kalau False, klik ulang tombol Algo Trading di MT5)")

mt5.shutdown()
