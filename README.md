# Bot Trading XAUUSD untuk MT5

Bot ini menjalankan strategi trend-following pada timeframe yang dipilih lewat
`TF_TREND` dan `TF_ENTRY` (konfigurasi aktif: M1/M1) dengan manajemen risiko
otomatis di MetaTrader 5.

## PERINGATAN PENTING

- **Tidak ada sistem trading yang bisa profit 100% atau profit konsisten setiap
  hari.** Bot ini dirancang dengan manajemen risiko yang disiplin, tapi tetap
  akan mengalami rugi di sebagian trade -- itu normal dan diperhitungkan lewat
  rasio risk-reward.
- **WAJIB dites dulu di akun demo minimal 1-3 bulan** sebelum dipakai di akun
  live, mencakup berbagai kondisi pasar (trending & sideways).
- Tersedia backtest sederhana, tetapi hasilnya bukan bukti strategi akan profit.

## Instalasi cepat

```powershell
git clone https://github.com/roufq/bot_trade.git trading
cd trading
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python main.py
```

Ikuti [INSTALLATION.md](INSTALLATION.md) untuk setup MT5, keamanan kredensial,
data AI, backtest, update repository, dan troubleshooting. Panduan notifikasi
tersedia di [TELEGRAM_SETUP.md](TELEGRAM_SETUP.md).

## Konfigurasi

Buka `config.py` dan sesuaikan:

- `MT5_LOGIN`, `MT5_PASSWORD`, `MT5_SERVER` -- detail akun MT5 Anda.
- `SYMBOL` agar sesuai nama instrumen broker.
- Token Telegram dan Chat ID disimpan sebagai environment variable, bukan di
  source code.

Semua parameter risiko (persen risiko per trade, drawdown limit, dll) sudah
diisi sesuai kesepakatan awal, tapi bisa disesuaikan di file yang sama.

## Menjalankan

```
python main.py
```

Bot akan berjalan terus-menerus (loop) selama terminal dibiarkan terbuka,
mengecek sinyal setiap `CHECK_INTERVAL_SECONDS` detik. Hentikan dengan
`Ctrl+C` -- bot akan mencatat log dan mengirim notifikasi Telegram saat
berhenti.

## Struktur file

| File | Fungsi |
|---|---|
| `config.py` | Semua parameter (risiko, strategi, koneksi) |
| `mt5_connector.py` | Komunikasi ke MT5 (hanya jalan di Windows) |
| `indicators.py` | Perhitungan EMA, RSI, ATR |
| `strategy.py` | Logika sinyal entry sesuai timeframe konfigurasi |
| `risk_manager.py` | Position sizing, SL/TP, cek drawdown harian |
| `trade_logger.py` | Logging ke `trade_log.csv` dan `system_log.csv` |
| `notifier.py` | Notifikasi Telegram |
| `main.py` | Loop utama yang menjalankan semuanya |
| `learner.py` | Adaptasi risiko dengan guardrail kualitas histori |
| `ai_trader.py` | Model ML opsional dengan evaluasi berbasis waktu |
| `data_quality.py` | Audit kelayakan closed trade untuk learning |

## Validasi data AI

Jalankan `python data_quality.py` sebelum training. Minimal 50 closed trade
valid diperlukan. Training otomatis ditolak
bila ticket duplikat, profit tidak bervariasi, atau data hanya berisi win/loss.
Model memakai 20% data paling baru sebagai pengujian out-of-sample.
Selama belum ada histori valid, bot memakai threshold cold-start yang lebih
rendah dengan risiko konservatif untuk mengumpulkan data awal.

## Keterbatasan

- Filter kalender ekonomi (menghindari trading saat rilis berita besar).
- Penyesuaian leverage dinamis Valetax (leverage turun otomatis di jam
  tertentu -- perlu ditambahkan sebagai pengecekan tambahan sebelum kirim
  order jika ingin dihindari trading di jam tersebut).
