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

## Cara AI belajar

Bot memakai dua lapisan pembelajaran. Learner adaptif menghitung win rate,
profit factor, expectancy uang, dan hasil rata-rata dalam satuan `R` (profit
dibagi risiko awal). Statistik dipisahkan menurut jenis setup, tetapi tidak
menurut arah buy/sell, lalu dibaurkan dengan statistik global agar sampel kecil
tidak membuat bot terlalu percaya diri. Identitas arah juga tidak menjadi fitur
model: buy dan sell dinilai setara berdasarkan kondisi chart.

Setelah minimal 50 closed trade valid, `python retrain_model.py` melatih model
klasifikasi probabilitas profit sekaligus model regresi expected `R`. Kandidat
model hanya dipakai jika lolos evaluasi out-of-sample untuk AUC, Brier score,
error expected-R, dan actual-R sinyal yang dipilih. Probabilitas tinggi saja
tidak cukup apabila expected-R di bawah batas.

Baseline drawdown harian disimpan di `runtime_state.json`, sehingga restart bot
tidak mereset batas kerugian hari tersebut.

Cooldown bersifat progresif untuk timeframe M1: tanpa jeda setelah profit,
60 detik setelah loss pertama, 3 menit setelah loss kedua, dan 10 menit mulai
loss ketiga. Tujuannya menjaga peluang entry tanpa menghapus proteksi ketika
kondisi pasar berulang kali tidak cocok.

Jika profit factor atau expectancy rolling melemah, bot berhenti 10 menit lalu
masuk `mode probe`: threshold entry dinaikkan 0,10 dan risiko target dipotong
40%. Dengan demikian kill-switch tidak mengalami deadlock, tetapi bot juga
tidak langsung kembali trading normal setelah performa negatif.

Setiap setup valid juga dicatat secara virtual ke `shadow_signal_log.csv`, baik
yang diterima maupun ditolak AI. Hasil SL/TP virtual ini memungkinkan evaluasi
apakah filter AI benar-benar menambah nilai tanpa mempertaruhkan uang pada
sinyal yang ditolak.

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

Sesuaikan konfigurasi berikut:

- Kredensial MT5 disimpan melalui environment variable `TRADING_MT5_LOGIN`,
  `TRADING_MT5_PASSWORD`, `TRADING_MT5_SERVER`, dan `TRADING_MT5_PATH`.
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

Proteksi runtime mencakup satu instance, spread/volatilitas, blackout berita
manual, cooldown, loss streak, drawdown harian/mingguan/equity peak,
break-even, trailing stop, directional exposure, larangan averaging-down,
broker/margin preflight, rolling performance kill-switch, model drift, dan
rekonsiliasi ticket setelah restart.

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
| `market_filters.py` | Spread, volatilitas, blackout, cooldown, loss streak |
| `position_manager.py` | Break-even dan trailing stop |
| `runtime_guard.py` | Single-instance lock dan state restart |
| `performance_report.py` | Statistik performa, spread, dan slippage |
| `execution_guard.py` | Validasi tick, stop level, volume, dan margin broker |
| `performance_guard.py` | Kill-switch profit factor, expectancy, dan deviasi loss |
| `news_filter.py` | Adapter kalender ekonomi opsional dengan cache |
| `model_monitor.py` | Deteksi penurunan AUC/Brier model aktif |
| `model_registry.py` | Versioning, promosi, dan rollback model |
| `retrain_model.py` | Audit dan retraining aman |

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
