"""
mt5_connector.py
Semua fungsi yang berkomunikasi langsung dengan terminal MT5.

PENTING: Modul ini HANYA bisa dijalankan di Windows dengan MT5 desktop
terinstall dan sedang berjalan (package MetaTrader5 tidak berjalan native
di Mac/Linux). Pastikan "Algo Trading" sudah diaktifkan di MT5 sebelum
menjalankan skrip ini.
"""

import time
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd

try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = None  # supaya file ini tetap bisa di-import untuk keperluan lain (mis. testing di non-Windows)

import config

TIMEFRAME_MAP = {
    "M1": "TIMEFRAME_M1",
    "M5": "TIMEFRAME_M5",
    "M15": "TIMEFRAME_M15",
    "M30": "TIMEFRAME_M30",
    "H1": "TIMEFRAME_H1",
    "H4": "TIMEFRAME_H4",
    "D1": "TIMEFRAME_D1",
}


def _require_mt5():
    if mt5 is None:
        raise RuntimeError(
            "Package MetaTrader5 tidak tersedia. Modul ini hanya bisa dijalankan "
            "di Windows dengan 'pip install MetaTrader5' dan MT5 desktop terinstall."
        )


def connect() -> bool:
    """Inisialisasi koneksi ke terminal MT5 dan login ke akun."""
    _require_mt5()

    init_kwargs = {}
    if config.MT5_PATH:
        init_kwargs["path"] = config.MT5_PATH

    if not mt5.initialize(**init_kwargs):
        print(f"[mt5_connector] initialize() gagal, error: {mt5.last_error()}")
        return False

    # Cek dulu apakah MT5 sudah dalam kondisi login (misal login manual
    # lewat desktop). Kalau sudah, TIDAK perlu login() eksplisit lagi --
    # memaksa re-login lewat Python sering menyebabkan IPC timeout meski
    # kredensialnya benar, karena terminal sudah punya sesi aktif.
    existing_account = mt5.account_info()
    already_logged_in = (
        existing_account is not None
        and (not config.MT5_LOGIN or existing_account.login == config.MT5_LOGIN)
    )

    if already_logged_in:
        print(f"[mt5_connector] Sudah login sebagai akun {existing_account.login}, skip login() eksplisit.")
    elif config.MT5_LOGIN and config.MT5_PASSWORD and config.MT5_SERVER:
        authorized = mt5.login(
            login=config.MT5_LOGIN,
            password=config.MT5_PASSWORD,
            server=config.MT5_SERVER,
        )
        if not authorized:
            print(f"[mt5_connector] login() gagal, error: {mt5.last_error()}")
            mt5.shutdown()
            return False

    terminal_info = mt5.terminal_info()
    if terminal_info is None or not terminal_info.trade_allowed:
        print(
            "[mt5_connector] PERINGATAN: Algo Trading belum aktif di MT5. "
            "Aktifkan tombol 'Algo Trading' di toolbar MT5 sebelum lanjut."
        )
        return False

    print("[mt5_connector] Koneksi ke MT5 berhasil.")
    return True


def disconnect() -> None:
    """Menutup koneksi ke MT5."""
    _require_mt5()
    mt5.shutdown()


def get_rates(symbol: str, timeframe: str, count: int = 300, closed_only: bool = True) -> Optional[pd.DataFrame]:
    """
    Mengambil data candle historis dari MT5.

    Parameters
    ----------
    symbol : nama instrumen, misal "XAUUSD"
    timeframe : salah satu dari TIMEFRAME_MAP keys, misal "M15", "H1"
    count : jumlah candle yang diambil (dari yang terbaru mundur ke belakang)
    """
    _require_mt5()

    tf_attr = TIMEFRAME_MAP.get(timeframe)
    if tf_attr is None:
        raise ValueError(f"Timeframe tidak dikenal: {timeframe}")
    tf_const = getattr(mt5, tf_attr)

    # start_pos=0 adalah candle yang masih terbentuk dan dapat berubah. Sinyal
    # trading memakai candle tertutup untuk menghindari intrabar repainting.
    start_pos = 1 if closed_only else 0
    rates = mt5.copy_rates_from_pos(symbol, tf_const, start_pos, count)
    if rates is None or len(rates) == 0:
        print(f"[mt5_connector] Gagal mengambil data rates untuk {symbol} {timeframe}: {mt5.last_error()}")
        return None

    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df = df.rename(columns={"tick_volume": "volume"})
    return df[["time", "open", "high", "low", "close", "volume"]]


def get_account_info() -> Optional[dict]:
    """Mengambil info akun: equity, balance, margin, dll."""
    _require_mt5()
    info = mt5.account_info()
    if info is None:
        print(f"[mt5_connector] Gagal mengambil account_info: {mt5.last_error()}")
        return None
    return info._asdict()


def get_symbol_info(symbol: str) -> Optional[dict]:
    """Mengambil info simbol: contract_size, tick_value, tick_size, volume_min, dll."""
    _require_mt5()
    info = mt5.symbol_info(symbol)
    if info is None:
        print(f"[mt5_connector] Gagal mengambil symbol_info untuk {symbol}: {mt5.last_error()}")
        return None
    if not info.visible:
        mt5.symbol_select(symbol, True)
        info = mt5.symbol_info(symbol)
    return info._asdict()


def get_current_prices(symbol: str) -> Optional[tuple[float, float]]:
    """Mengambil harga Ask dan Bid saat ini (real-time)."""
    _require_mt5()
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        return None
    return tick.ask, tick.bid


def get_tick_info(symbol: str) -> Optional[dict]:
    _require_mt5()
    tick = mt5.symbol_info_tick(symbol)
    return tick._asdict() if tick is not None else None


def calculate_order_margin(symbol: str, order_type: str, lot_size: float, price: float) -> Optional[float]:
    _require_mt5()
    mt5_type = mt5.ORDER_TYPE_BUY if order_type == "buy" else mt5.ORDER_TYPE_SELL
    margin = mt5.order_calc_margin(mt5_type, symbol, lot_size, price)
    return float(margin) if margin is not None else None


def get_open_positions(symbol: str) -> list:
    """Mengambil semua posisi terbuka untuk simbol tertentu."""
    _require_mt5()
    positions = mt5.positions_get(symbol=symbol)
    if positions is None:
        return []
    return list(positions)


def modify_position_sltp(position_ticket: int, symbol: str, sl_price: float, tp_price: float) -> dict:
    """Ubah SL/TP posisi tanpa mengubah volume."""
    _require_mt5()
    request = {
        "action": mt5.TRADE_ACTION_SLTP,
        "position": int(position_ticket),
        "symbol": symbol,
        "sl": float(sl_price),
        "tp": float(tp_price),
    }
    result = mt5.order_send(request)
    if result is None:
        return {"success": False, "error": f"order_send gagal: {mt5.last_error()}"}
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        return {"success": True}
    return {"success": False, "error": f"retcode={result.retcode}, comment={result.comment}"}


def get_recent_new_position_ticket(symbol: str, existing_tickets: set[int] | list | None = None, max_retries: int = 5,
                                   retry_delay_seconds: float = 0.5) -> Optional[int]:
    """Mencari ticket posisi baru yang belum ada di daftar ticket lama."""
    if existing_tickets is None:
        previous_ticket_set = set()
    elif isinstance(existing_tickets, set):
        previous_ticket_set = existing_tickets
    else:
        previous_ticket_set = {
            p.ticket if hasattr(p, "ticket") else int(p)
            for p in existing_tickets
            if p is not None
        }

    for attempt in range(max_retries):
        current_tickets = {p.ticket for p in get_open_positions(symbol)}
        new_tickets = current_tickets - previous_ticket_set
        if new_tickets:
            return max(new_tickets)
        time.sleep(retry_delay_seconds)
    return None


def get_closed_deal_by_position(position_ticket: int, max_retries: int = 5,
                                 retry_delay_seconds: float = 1.0) -> Optional[dict]:
    """
    Mengambil detail deal penutup (exit) untuk sebuah posisi yang baru tertutup,
    berdasarkan ticket posisinya. Dipakai untuk mendapatkan profit/rugi final.

    Otomatis mencoba ulang beberapa kali dengan jeda -- karena riwayat deal
    kadang belum terindeks di server MT5 tepat saat posisi baru saja tertutup,
    terutama saat interval pengecekan bot sangat cepat (mode scalping).
    """
    _require_mt5()

    for attempt in range(max_retries):
        # Bentuk API khusus `position=` harus dipanggil tanpa rentang tanggal.
        # Menggabungkan date_from/date_to dengan keyword position pada beberapa
        # versi MT5 dapat mengembalikan seluruh histori, lalu profit semua posisi
        # ikut terjumlah sebagai satu closed trade.
        deals = mt5.history_deals_get(position=position_ticket)
        if deals:
            exits = [
                deal for deal in deals
                if deal.entry == mt5.DEAL_ENTRY_OUT
                and int(getattr(deal, "position_id", 0) or 0) == int(position_ticket)
            ]
            if exits:
                exits.sort(key=lambda d: getattr(d, "time_msc", getattr(d, "time", 0)))
                latest = exits[-1]._asdict()
                total_volume = sum(float(getattr(d, "volume", 0.0)) for d in exits)
                if total_volume > 0:
                    latest["price"] = sum(float(d.price) * float(d.volume) for d in exits) / total_volume
                latest["volume"] = total_volume
                latest["profit"] = sum(float(getattr(d, "profit", 0.0)) for d in exits)
                latest["swap"] = sum(float(getattr(d, "swap", 0.0)) for d in exits)
                latest["commission"] = sum(float(getattr(d, "commission", 0.0)) for d in exits)
                latest["fee"] = sum(float(getattr(d, "fee", 0.0)) for d in exits)
                return latest

        if attempt < max_retries - 1:
            time.sleep(retry_delay_seconds)

    return None


def get_position_ticket_from_deal(
    order_id: str | int | None = None,
    deal_id: str | int | None = None,
    symbol: str | None = None,
    max_retries: int = 8,
    retry_delay_seconds: float = 0.5,
) -> int | None:
    """Cari ticket posisi untuk order/last deal yang baru dieksekusi."""
    _require_mt5()

    for attempt in range(max_retries):
        now = datetime.now()
        deals = mt5.history_deals_get(now - timedelta(minutes=5), now)
        if deals:
            ordered_deals = sorted(
                deals,
                key=lambda d: getattr(d, "time_msc", getattr(d, "time", 0)),
                reverse=True,
            )
            for deal in ordered_deals:
                if deal.entry != mt5.DEAL_ENTRY_IN:
                    continue
                if deal_id and str(getattr(deal, 'deal', '')) == str(deal_id):
                    position_ticket = int(getattr(deal, 'position', 0) or 0)
                    if position_ticket:
                        return position_ticket
                if order_id and str(getattr(deal, 'order', '')) == str(order_id):
                    position_ticket = int(getattr(deal, 'position', 0) or 0)
                    if position_ticket:
                        return position_ticket
                if not order_id and not deal_id and symbol and getattr(deal, 'symbol', '') == symbol:
                    # Fallback simbol hanya aman bila caller tidak punya ID eksplisit.
                    position_ticket = int(getattr(deal, 'position', 0) or 0)
                    if position_ticket:
                        return position_ticket
        if attempt < max_retries - 1:
            time.sleep(retry_delay_seconds)

    return None


def send_market_order(symbol: str, order_type: str, lot_size: float,
                       sl_price: float, tp_price: float, comment: str = "auto-bot") -> dict:
    """
    Mengirim order market buy/sell dengan SL/TP. Otomatis mencoba beberapa
    filling mode (FOK, IOC, RETURN) kalau mode pertama ditolak broker
    (retcode 10030 'Unsupported filling mode').

    Returns
    -------
    dict berisi status keberhasilan dan detail hasil dari MT5.
    """
    _require_mt5()

    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        return {"success": False, "error": "Gagal mengambil harga tick terkini"}

    sym_info = mt5.symbol_info(symbol)
    if sym_info is None:
        return {"success": False, "error": "Gagal mengambil symbol_info untuk tentukan filling mode"}

    # Susun urutan filling mode yang dicoba: mulai dari yang terdeteksi
    # didukung broker, lalu fallback ke mode lain kalau masih ditolak.
    # Pakai nilai integer langsung (bukan konstanta mt5.SYMBOL_FILLING_*)
    # karena tidak semua versi package MetaTrader5 mengekspos konstanta itu.
    FILLING_FOK_BIT = 1
    FILLING_IOC_BIT = 2
    filling_mode = sym_info.filling_mode
    candidates = []
    if filling_mode & FILLING_FOK_BIT:
        candidates.append(mt5.ORDER_FILLING_FOK)
    if filling_mode & FILLING_IOC_BIT:
        candidates.append(mt5.ORDER_FILLING_IOC)
    candidates.append(mt5.ORDER_FILLING_RETURN)
    # Hilangkan duplikat sambil pertahankan urutan
    candidates = list(dict.fromkeys(candidates))

    price = tick.ask if order_type == "buy" else tick.bid
    mt5_order_type = mt5.ORDER_TYPE_BUY if order_type == "buy" else mt5.ORDER_TYPE_SELL

    last_error = None
    for type_filling in candidates:
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot_size,
            "type": mt5_order_type,
            "price": price,
            "sl": sl_price,
            "tp": tp_price,
            "deviation": 20,
            "magic": 234000,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": type_filling,
        }

        check = mt5.order_check(request)
        if check is None:
            last_error = f"order_check gagal: {mt5.last_error()}"
            continue
        if int(getattr(check, "retcode", -1)) != 0:
            last_error = f"order_check retcode={check.retcode}, comment={getattr(check, 'comment', '')}"
            if int(getattr(check, "retcode", -1)) != 10030:
                break
            continue

        result = mt5.order_send(request)

        if result is None:
            last_error = f"order_send gagal: {mt5.last_error()}"
            continue

        if result.retcode == mt5.TRADE_RETCODE_DONE:
            return {
                "success": True,
                "order_id": getattr(result, "order", None),
                "deal_id": getattr(result, "deal", None),
                "price": result.price,
                "volume": result.volume,
            }

        last_error = f"retcode={result.retcode}, comment={result.comment}"
        if result.retcode != 10030:
            # Bukan soal filling mode -- tidak ada gunanya coba mode lain
            break

    return {"success": False, "error": last_error}
