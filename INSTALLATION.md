# Instalasi dan Setup Bot Trading MT5 XAUUSD

Dokumen ini menjelaskan cara memasang, mengkonfigurasi, dan menjalankan bot trading MT5 untuk XAUUSD di Windows.

---

## Prasyarat

1. Windows 10/11.
2. MetaTrader 5 desktop terinstal dan berfungsi.
3. MetaTrader 5 sudah login ke akun demo atau live.
4. Tombol **Algo Trading** aktif di toolbar MT5.
5. Python 3.14 (direkomendasikan) atau Python 3.11.
6. Akses internet untuk notifikasi Telegram dan koneksi broker.

---

## Instalasi Python dan Virtual Environment

1. Buka PowerShell di folder project:

   ```powershell
   cd C:\trading
   ```

2. Buat virtual environment:

   ```powershell
   python -m venv .venv
   ```

3. Aktifkan virtual environment:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

4. Perbarui `pip` dan instal dependensi:

   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

---

## Konfigurasi `config.py`

Buka file `config.py` dan sesuaikan parameter berikut:

- `MT5_LOGIN`: nomor akun MT5 Anda.
- `MT5_PASSWORD`: password akun MT5.
- `MT5_SERVER`: nama server broker MT5.
- `MT5_PATH`: opsional, path ke `terminal64.exe` jika perlu eksplisit.
- `SYMBOL`: instrumen trading, default `XAUUSD.vx`.
- `TRADING_HOUR_START` dan `TRADING_HOUR_END`: jam trading aktif.
- `RISK_PERCENT_PER_TRADE`: persentase equity yang dirisikokan setiap trade.
- `MAX_DAILY_DRAWDOWN_PERCENT`: batas drawdown harian supaya bot berhenti.
- Environment variable `TRADING_TELEGRAM_BOT_TOKEN` dan
  `TRADING_TELEGRAM_CHAT_ID`: untuk notifikasi Telegram. Kredensial tidak
  disimpan di source code.

> Catatan: jangan commit kredensial akun live jika Anda menggunakan repositori publik.

Panduan pembuatan bot, Chat ID, environment variable, pengujian, dan
troubleshooting Telegram tersedia di `TELEGRAM_SETUP.md`.

---

## Menjalankan Bot

Setelah konfigurasi selesai dan venv aktif, jalankan:

```powershell
python main.py
```

Bot akan:

- memeriksa saldo dan drawdown harian,
- memindai sinyal entry berdasarkan strategi multi-timeframe,
- menghitung ukuran lot, SL, TP,
- mengirim order market ke MT5,
- mencatat log trading ke CSV,
- mengirim notifikasi jika broker atau sistem error.

Hentikan bot dengan `Ctrl+C`.

---

## Perintah jika `python main.py` menggunakan interpreter yang salah

Jika perintah `python` di terminal Anda masih menunjuk ke interpreter global lain, gunakan path lengkap ke virtualenv:

```powershell
C:\trading\.venv\Scripts\python.exe main.py
```

---

## Struktur File Utama

- `config.py` - parameter koneksi, strategi, dan manajemen risiko.
- `mt5_connector.py` - komunikasi dengan MT5 dan eksekusi order.
- `indicators.py` - perhitungan indikator teknikal (EMA, RSI, ATR).
- `strategy.py` - logika sinyal entry dengan filter tren dan momentum.
- `risk_manager.py` - ukuran lot, level SL/TP, batas risiko.
- `trade_logger.py` - logging trade dan event sistem ke CSV.
- `notifier.py` - notifikasi Telegram.
- `learner.py` - logika adaptif berbasis riwayat closed trade.
- `ai_trader.py` - scaffold ML untuk inferensi dan training.
- `main.py` - loop utama bot.

---

## File Log dan Data

Bot mencatat ke file berikut:

- `trade_log.csv` - data entry trade beserta fitur ML.
- `closed_trade_log.csv` - data trade yang sudah tertutup untuk learning.
- `system_log.csv` - event sistem, error, dan keputusan penting.

---

## Dependensi

- `MetaTrader5`
- `pandas`
- `numpy`
- `requests`
- `scikit-learn`
- `joblib`

Semua dependensi sudah dimasukkan di `requirements.txt`.

---

## Tips Penting

- Uji di akun demo selama minimal 1-3 bulan sebelum live.
- Periksa timezone MT5 dan jam trading di `config.py`.
- Pastikan `Algo Trading` aktif.
- Lihat file log jika terjadi error atau order gagal.

---

## Menjalankan Training ML (opsional)

Audit kualitas data lebih dulu:

```powershell
python data_quality.py
```

Jika hasilnya `VALID`, latih model:

```powershell
python -c "import ai_trader; ai_trader.train_model()"
```

Model akan disimpan di `ml_model.joblib`.

---

## Penyesuaian Lanjutan

- Set `AI_FORCE_MODEL_ONLY = True` di `config.py` untuk menolak entry jika model ML belum tersedia.
- Ubah `AI_MIN_PROBA_ENTRY` untuk menaikkan/menurunkan threshold confidence model.
- Sesuaikan `RISK_PERCENT_PER_TRADE` dan `MAX_DAILY_DRAWDOWN_PERCENT` untuk gaya manajemen risiko Anda.
