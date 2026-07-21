"""
notifier.py
Mengirim notifikasi ke Telegram saat bot start, stop, error, atau
kena limit drawdown harian.

Cara setup:
1. Chat ke @BotFather di Telegram, ketik /newbot, ikuti instruksinya.
2. Simpan token ke environment variable TRADING_TELEGRAM_BOT_TOKEN.
3. Chat ke bot Anda sekali (apa saja), lalu buka:
   https://api.telegram.org/bot<TOKEN>/getUpdates
   Cari nilai "chat":{"id": ...} -> itu chat ID Anda.
4. Simpan ID ke environment variable TRADING_TELEGRAM_CHAT_ID.
"""

import requests

import config


def send_telegram_message(message: str) -> bool:
    """
    Mengirim pesan ke Telegram. Mengembalikan True jika berhasil,
    False jika gagal (tidak melempar exception supaya bot utama tidak crash
    hanya karena notifikasi gagal terkirim).
    """
    if not config.TELEGRAM_ENABLED:
        return False

    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        print("[notifier] Telegram belum dikonfigurasi (token/chat_id kosong)")
        return False

    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": config.TELEGRAM_CHAT_ID, "text": message}

    try:
        response = requests.post(url, data=payload, timeout=10)
        if response.ok:
            return True
        try:
            description = response.json().get("description", "respons tidak dikenal")
        except ValueError:
            description = response.text[:200] or "respons tidak dikenal"
        print(f"[notifier] Telegram menolak pesan (HTTP {response.status_code}): {description}")
        return False
    except requests.RequestException as e:
        # Jangan cetak exception lengkap karena URL request mengandung token bot.
        print(f"[notifier] Gagal terhubung ke Telegram: {type(e).__name__}")
        return False


def notify_bot_started() -> None:
    send_telegram_message(f"Bot trading {config.SYMBOL} dimulai.")


def notify_bot_stopped(reason: str) -> None:
    send_telegram_message(f"Bot trading {config.SYMBOL} berhenti.\nAlasan: {reason}")


def notify_daily_drawdown_hit(drawdown_percent: float) -> None:
    send_telegram_message(
        f"PERINGATAN: Drawdown harian {config.SYMBOL} mencapai {drawdown_percent:.2f}% "
        f"(limit: {config.MAX_DAILY_DRAWDOWN_PERCENT}%).\nBot dihentikan untuk sisa hari ini."
    )


def notify_trade_opened(signal: str, lot_size: float, entry_price: float,
                         sl_price: float, tp_price: float) -> None:
    send_telegram_message(
        f"Order {signal.upper()} {config.SYMBOL} dibuka.\n"
        f"Lot: {lot_size}\nEntry: {entry_price}\nSL: {sl_price}\nTP: {tp_price}"
    )


def notify_trade_closed(signal: str, lot_size: float, close_price: float,
                         profit: float, balance_after: float) -> None:
    hasil = "PROFIT" if profit >= 0 else "RUGI"
    send_telegram_message(
        f"Posisi {signal.upper()} {config.SYMBOL} ditutup.\n"
        f"Lot: {lot_size}\nHarga tutup: {close_price}\n"
        f"Hasil: {hasil} ${profit:.2f}\n"
        f"Saldo sekarang: ${balance_after:.2f}"
    )


def notify_error(error_detail: str) -> None:
    send_telegram_message(f"ERROR pada bot {config.SYMBOL}:\n{error_detail}")
