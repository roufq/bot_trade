"""
test_connection.py
Jalankan file ini SEBELUM main.py untuk memastikan koneksi ke MT5 berhasil,
tanpa risiko bot langsung mencoba kirim order.

Jalankan dengan: python test_connection.py
"""

import mt5_connector
import config


def main():
    print("Mencoba konek ke MT5...")
    success = mt5_connector.connect()

    if not success:
        print("\nKONEKSI GAGAL. Cek kembali:")
        print("- MT5 desktop sudah terbuka dan login?")
        print("- Tombol 'Algo Trading' di MT5 sudah aktif (hijau)?")
        print("- MT5_LOGIN, MT5_PASSWORD, MT5_SERVER di config.py sudah benar?")
        return

    print("\nKONEKSI BERHASIL.\n")

    # Tes ambil info akun
    account = mt5_connector.get_account_info()
    if account:
        print(f"Nama akun   : {account.get('name')}")
        print(f"Login       : {account.get('login')}")
        print(f"Server      : {account.get('server')}")
        print(f"Balance     : {account.get('balance')}")
        print(f"Equity      : {account.get('equity')}")
        print(f"Currency    : {account.get('currency')}")

    # Tes ambil info simbol XAUUSD
    print(f"\nMencoba ambil info simbol {config.SYMBOL}...")
    symbol_info = mt5_connector.get_symbol_info(config.SYMBOL)
    if symbol_info:
        print(f"Symbol ditemukan: {config.SYMBOL}")
        print(f"Contract size    : {symbol_info.get('trade_contract_size')}")
        print(f"Tick value       : {symbol_info.get('trade_tick_value')}")
        print(f"Tick size        : {symbol_info.get('trade_tick_size')}")
        print(f"Volume min/max   : {symbol_info.get('volume_min')} / {symbol_info.get('volume_max')}")
    else:
        print(f"GAGAL menemukan simbol {config.SYMBOL}. Cek nama simbol persis di MT5 "
              f"(kadang broker pakai suffix, misal 'XAUUSD.a' atau 'XAUUSDm').")

    # Tes ambil data candle
    print(f"\nMencoba ambil data candle H1...")
    df_h1 = mt5_connector.get_rates(config.SYMBOL, "H1", count=5)
    if df_h1 is not None:
        print("Data H1 berhasil diambil, 5 candle terakhir:")
        print(df_h1)
    else:
        print("GAGAL mengambil data candle.")

    mt5_connector.disconnect()
    print("\nSelesai, koneksi ditutup.")


if __name__ == "__main__":
    main()
