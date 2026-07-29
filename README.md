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

Setelah minimal 200 sampel gabungan yang valid, `python retrain_model.py` melatih model
klasifikasi probabilitas profit sekaligus model regresi expected `R`. Kandidat
model hanya dipakai jika lolos evaluasi out-of-sample untuk AUC, Brier score,
error expected-R, dan actual-R sinyal yang dipilih. Probabilitas tinggi saja
tidak cukup apabila expected-R di bawah batas.

Versi 1.4.0 menambahkan historical replay dan shadow learning. Tombol
`Bangun Dataset` menjalankan strategi A-L pada candle tertutup MT5, memberi
label SL/TP secara konservatif, dan menyimpan snapshot fitur sebelum outcome
terjadi. `Training AI` otomatis membangun replay bila sampel belum mencapai
minimum 200, lalu menggabungkan trade nyata, shadow reject resolved, dan replay
historis dengan deduplikasi per menit/arah. Test out-of-sample wajib berisi
minimal 40 sampel. Kandidat yang ditolak disimpan sebagai laporan, bukan
dipaksakan menjadi model aktif.

Baseline drawdown harian disimpan di `runtime_state.json`, sehingga restart bot
tidak mereset batas kerugian hari tersebut.

Sejak versi 1.3.1, state risiko terikat pada login dan server MT5. First-run,
migrasi dari versi lama, atau pergantian akun akan membuat baseline baru dari
equity akun yang sedang aktif. Dengan demikian peak milik akun lain tidak dapat
memicu drawdown palsu, sementara restart pada akun yang sama tetap mempertahankan
proteksi drawdown.

Cooldown bersifat progresif untuk timeframe M1: tanpa jeda setelah profit,
60 detik setelah loss pertama, 3 menit setelah loss kedua, dan 10 menit mulai
loss ketiga. Tujuannya menjaga peluang entry tanpa menghapus proteksi ketika
kondisi pasar berulang kali tidak cocok.

Jika profit factor atau expectancy rolling melemah, bot berhenti 10 menit lalu
masuk `mode probe`: threshold entry dinaikkan 0,10 dan risiko target dipotong
40%. Dengan demikian kill-switch tidak mengalami deadlock, tetapi bot juga
tidak langsung kembali trading normal setelah performa negatif.

Filter spread memiliki tiga tingkat. Spread sampai 20% ATR diproses normal;
20--25% ATR menaikkan threshold 0,05 dan menurunkan target risiko 15%;
25--35% ATR menaikkan threshold 0,10 dan menurunkan target risiko 35%.
Spread di atas 35% ATR atau 50 points tetap ditolak.

## Strategi modular A-L

Engine memakai sumber sinyal yang dapat diaudit dan dinonaktifkan secara terpisah:

- **A**: EMA, RSI, ATR, crossover, continuation, dan momentum yang sudah ada.
- **B**: FVG dari candle tertutup H1/M15 dengan rejection pada candle tertutup M1.
- **C**: market structure (HH/HL/LH/LL, BOS, dan CHoCH).
- **D**: buy-side/sell-side liquidity sweep dan reclaim.
- **E**: support/resistance, rejection, breakout, dan breakdown.
- **F**: mitigasi bullish/bearish order block.
- **G**: retest supply/demand setelah departure kuat.
- **H**: displacement berdasarkan body/range dan ATR.
- **I**: lokasi premium/discount dalam dealing range.
- **J**: engulfing dan rejection candlestick.
- **K**: ekspansi tick-volume.
- **L**: konteks active session; modul ini tidak membuka posisi sendiri.

Jika hanya A atau hanya B yang valid dan strategi lain netral, entry tetap boleh
dilakukan dengan pengali risiko solo (default 0,50). Jika A dan B searah, sumber
sinyal menjadi `A_PLUS_B` dengan risiko normal--bukan risiko ganda. Jika arah A
dan B berlawanan, entry dibatalkan. Setiap entry mencatat `strategy_source`,
sinyal A/B, timeframe FVG, dan batas zona agar performa `A_ONLY`, `B_ONLY`, dan
`A_PLUS_B` dapat dibandingkan. FVG yang telah terisi penuh atau melewati umur
maksimum tidak digunakan kembali.

Strategi C-L menghasilkan arah dan skor sendiri. Entry modular membutuhkan
minimal dua modul searah, skor gabungan minimum, dan sedikitnya satu setup utama
dari C-G. H/I/J/K hanya dapat menjadi konfirmasi. Konflik kuat membatalkan entry,
bukan dirata-ratakan. Skor setiap teknik disimpan di `trade_log.csv` dan menjadi
fitur model berikutnya; model lama tetap memakai kontrak fitur yang tersimpan
di bundle agar upgrade tidak merusak inferensi.

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

Pengguna yang menginginkan tombol Start/Stop dan form konfigurasi dapat
menjalankan aplikasi desktop. Panduan source dan build EXE tersedia di
[DESKTOP_SETUP.md](DESKTOP_SETUP.md).

Paket untuk komputer tanpa Python dibuat sebagai
`installer_output/AITradingDesktop-Setup-1.4.3.exe`. MetaTrader 5 tetap wajib
terpasang dan login.

## Konfigurasi

Aplikasi desktop menyediakan profil **Konservatif**, **Seimbang**, dan **Aktif**
sebagai titik awal. Setiap pengguna dapat mengubah sendiri risiko, jumlah posisi,
  spread/ATR, strategi A/B, parameter FVG, periode EMA/RSI/ATR, SL dan TP berbasis ATR, jarak entry, rentang
volatilitas, break-even, trailing stop, serta jam trading. Semua nilai divalidasi
sebelum disimpan. Preset maupun konfigurasi manual tidak menjamin profit; proteksi
risiko internal tetap aktif.

Versi 1.3.1 memakai satu **Folder data terpadu** untuk engine source dan
desktop. Tombol **Import CSV Pengalaman** menggabungkan entry, closed trade, dan
shadow signal berdasarkan ticket tanpa menggandakan pengalaman. Tombol
**Export CSV Pengalaman** membuat salinan portabel tanpa password MT5, token
Telegram, atau konfigurasi rahasia. Backup dibuat sebelum import memperbarui
file tujuan.

Versi 1.3.1 juga menyediakan pengaturan jarak momentum dan tambahan threshold
probe/spread. Default mode aktif lebih longgar: threshold dasar 0,45 menjadi
sekitar 0,48 ketika probe dan spread tinggi aktif, sementara target risiko tetap
diperkecil selama performa rolling melemah.

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
| `technical_strategies.py` | Detector independen market structure, liquidity, SNR, OB, supply/demand, displacement, premium/discount, candle, volume, dan session |
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
