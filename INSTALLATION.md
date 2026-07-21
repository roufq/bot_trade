# Instalasi Bot Trading MT5 XAUUSD dari GitHub

Panduan ini ditujukan untuk Windows 10/11. Bot berkomunikasi langsung dengan
MetaTrader 5 desktop dan harus diuji pada akun demo sebelum digunakan pada akun
live.

## Peringatan

- Tidak ada jaminan profit atau win rate tertentu.
- Gunakan akun demo minimal 1–3 bulan dan evaluasi drawdown serta biaya broker.
- Jangan commit token Telegram, password MT5, file `.env`, log CSV, atau model
  ML ke GitHub.
- Jalankan hanya satu instance `main.py`.

## Prasyarat

1. Windows 10/11.
2. Git.
3. Python 3.11 direkomendasikan untuk kompatibilitas package MT5.
4. MetaTrader 5 desktop sudah terpasang dan login ke akun demo.
5. Tombol **Algo Trading** pada MT5 aktif.
6. Symbol broker untuk emas tersedia, misalnya `XAUUSD.vx` atau `XAUUSD`.

Periksa instalasi:

```powershell
git --version
python --version
```

## Clone repository

```powershell
cd C:\
git clone https://github.com/roufq/bot_trade.git trading
cd C:\trading
```

Jika folder `C:\trading` sudah ada, jangan menjalankan clone di atasnya. Masuk
ke folder tersebut dan gunakan `git pull` hanya jika perubahan lokal sudah
diamankan.

## Virtual environment dan dependency

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Jika PowerShell menolak aktivasi script:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Alternatif tanpa aktivasi:

```powershell
.\.venv\Scripts\python.exe main.py
```

Pastikan interpreter project digunakan:

```powershell
python -c "import sys; print(sys.executable)"
```

Output seharusnya mengarah ke `C:\trading\.venv\Scripts\python.exe`.

## Setup MetaTrader 5

1. Buka MT5 dan login ke akun demo.
2. Aktifkan **Algo Trading**.
3. Pastikan symbol emas tampil di Market Watch.
4. Simpan kredensial MT5 melalui environment variable (opsional bila terminal
   sudah login pada akun yang benar):

```powershell
$env:TRADING_MT5_LOGIN="12345678"
$env:TRADING_MT5_PASSWORD="PASSWORD_ANDA"
$env:TRADING_MT5_SERVER="NAMA-SERVER"
$env:TRADING_MT5_PATH="C:\Program Files\MetaTrader 5\terminal64.exe"
```

Sesuaikan hanya `SYMBOL` di `config.py` bila nama instrumen broker berbeda.
Jika MT5 sudah login, variabel koneksi dapat dikosongkan dan connector memakai
sesi aktif. Gunakan `SetEnvironmentVariable(..., "User")` seperti panduan
Telegram bila kredensial perlu disimpan permanen.

Uji koneksi:

```powershell
python test_connection.py
```

## Setup Telegram

Telegram dikonfigurasi melalui environment variable, bukan dengan menempelkan
token ke `config.py`:

```powershell
$env:TRADING_TELEGRAM_BOT_TOKEN="TOKEN_BARU_ANDA"
$env:TRADING_TELEGRAM_CHAT_ID="CHAT_ID_ANDA"
```

Periksa dan uji:

```powershell
python -c "import config; print(config.TELEGRAM_ENABLED)"
python -c "import notifier; print(notifier.send_telegram_message('Tes notifikasi trading'))"
```

Panduan lengkap, termasuk konfigurasi permanen dan troubleshooting
`chat not found`, tersedia di [TELEGRAM_SETUP.md](TELEGRAM_SETUP.md).

## Menjalankan test

```powershell
python -m unittest discover -s tests -v
```

Semua test harus lulus sebelum bot dijalankan.

## Menjalankan bot

```powershell
python main.py
```

Bot akan mengambil candle MT5 yang sudah tertutup, mengevaluasi sinyal,
menghitung risiko, mengirim order, mencatat entry/exit, dan mengirim notifikasi.
Hentikan secara normal dengan `Ctrl+C`.

Bot juga memiliki single-instance lock, filter spread/volatilitas, blackout
berita manual, cooldown setelah trade, loss-streak pause, drawdown
harian/mingguan/equity-peak, break-even, dan trailing stop. Blackout berita
diisi lewat environment variable, contoh:

```powershell
$env:TRADING_NEWS_BLACKOUT_WINDOWS="13:25-13:40,19:55-20:15"
```

Jam tersebut mengikuti waktu lokal komputer. Daftar harus diperbarui sesuai
jadwal berita; project tidak mengunduh kalender ekonomi otomatis.

## Data lokal dan AI

File berikut dibuat atau diperbarui secara lokal dan sengaja tidak disimpan di
GitHub:

- `trade_log.csv`
- `closed_trade_log.csv`
- `system_log.csv`
- `backtest_trades.csv`
- `backtest_equity_curve.csv`
- `ml_model.joblib`

Karena data tersebut tidak ikut repository, instalasi baru memulai histori AI
dari nol. Audit data dengan:

```powershell
python data_quality.py
```

Status `INVALID` dengan alasan `baru N trade valid` adalah normal sebelum ada
minimal 50 closed trade yang berisi variasi profit dan loss.

Jika audit menghasilkan `VALID`, jalankan training:

```powershell
python -c "import ai_trader; ai_trader.train_model()"
```

Model akan disimpan sebagai `ml_model.joblib`. Model dan histori dari akun atau
broker lain tidak otomatis cocok dengan kondisi broker Anda.

Lihat statistik berjalan:

```powershell
python performance_report.py
```

Laporan mencakup win rate, profit factor, expectancy, rata-rata win/loss, loss
streak, drawdown closed balance, spread, dan slippage.

## Backtest

Pastikan MT5 aktif dan memiliki data historis, kemudian jalankan:

```powershell
python backtest.py
```

Hasil backtest bukan jaminan performa masa depan. Periksa spread, komisi,
slippage, profit factor, dan maximum drawdown sebelum mengambil keputusan.

## Update dari GitHub

Hentikan bot dengan `Ctrl+C`, lalu periksa perubahan lokal:

```powershell
git status
git pull
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

Jangan menjalankan `git reset --hard` karena dapat menghapus perubahan lokal.

## Troubleshooting singkat

### `ModuleNotFoundError`

Aktifkan `.venv` atau gunakan interpreter lengkap:

```powershell
.\.venv\Scripts\python.exe main.py
```

### Telegram tidak aktif

```powershell
python -c "import config; print(config.TELEGRAM_ENABLED)"
```

Jika `False`, ikuti [TELEGRAM_SETUP.md](TELEGRAM_SETUP.md).

### Bot tidak entry

Baca alasan pada terminal dan `system_log.csv`. Penolakan dapat berasal dari
sinyal, spread/kondisi pasar, threshold learning, batas posisi, drawdown,
risiko minimum lot, atau respons broker.

### Bot berhenti pada drawdown

Bot menggunakan `MAX_DAILY_DRAWDOWN_PERCENT` di `config.py`. Acuannya adalah
equity awal hari dan mencakup floating profit/loss.
