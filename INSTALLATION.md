# Panduan Instalasi Bot Trading MT5 untuk Pemula

Panduan ini menjelaskan instalasi dari komputer Windows yang belum memiliki
Python sampai bot berhasil berjalan. Ikuti langkah secara berurutan dan gunakan
akun **demo** terlebih dahulu.

## Sebelum memulai

- Bot tidak menjamin profit dan tetap dapat mengalami kerugian.
- Gunakan Windows 10 atau Windows 11.
- Jangan memakai akun live sebelum pengujian demo minimal 1--3 bulan.
- Jangan membagikan password MT5, token Telegram, atau API key.
- Jangan menempelkan kredensial ke `config.py` atau mengunggahnya ke GitHub.
- Jalankan hanya satu `main.py`.

## 1. Instal Python

1. Buka `https://www.python.org/downloads/windows/`.
2. Unduh Python 3.11 versi 64-bit.
3. Jalankan installer.
4. Pada halaman pertama, centang **Add python.exe to PATH**.
5. Pilih **Install Now**.
6. Setelah selesai, tutup installer dan buka PowerShell baru.

Cara membuka PowerShell:

1. Tekan tombol Windows.
2. Ketik `PowerShell`.
3. Buka **Windows PowerShell**.

Periksa Python:

```powershell
python --version
python -m pip --version
```

Versi Python seharusnya dimulai dengan `Python 3.11`. Jika perintah `python`
tidak ditemukan, tutup PowerShell dan buka kembali. Jika masih gagal, instal
ulang Python dan pastikan **Add python.exe to PATH** dicentang.

## 2. Instal Git

1. Buka `https://git-scm.com/download/win`.
2. Unduh dan jalankan installer.
3. Untuk pengguna pemula, gunakan pilihan bawaan dengan menekan **Next** sampai
   instalasi selesai.
4. Tutup dan buka kembali PowerShell.

Periksa Git:

```powershell
git --version
```

## 3. Instal MetaTrader 5

1. Unduh MetaTrader 5 dari broker yang akan digunakan.
2. Instal dan buka terminal MT5.
3. Login ke **akun demo**.
4. Catat nomor login dan nama server dari informasi akun.
5. Aktifkan tombol **Algo Trading** di bagian atas MT5.
6. Buka **Market Watch** dengan `Ctrl+M`.
7. Klik kanan Market Watch, pilih **Symbols**, lalu tampilkan simbol emas.
8. Catat nama simbol persis dari broker, misalnya `XAUUSD`, `XAUUSD.vx`, atau
   nama lain.

Biarkan terminal MT5 terbuka selama bot berjalan.

## 4. Unduh project dari GitHub

Buka PowerShell, lalu jalankan:

```powershell
cd C:\
git clone https://github.com/roufq/bot_trade.git trading
cd C:\trading
```

Periksa isi folder:

```powershell
Get-ChildItem
```

File seperti `main.py`, `config.py`, dan `requirements.txt` harus terlihat.

Jika muncul pesan bahwa folder `trading` sudah ada, jangan melakukan clone
ulang. Gunakan:

```powershell
cd C:\trading
git status
```

## 5. Buat virtual environment

Virtual environment memisahkan package bot dari Python lain di komputer:

```powershell
cd C:\trading
python -m venv .venv
```

Aktifkan:

```powershell
.\.venv\Scripts\Activate.ps1
```

Jika aktivasi ditolak PowerShell:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Jawab `Y`, tutup PowerShell, buka lagi, kemudian:

```powershell
cd C:\trading
.\.venv\Scripts\Activate.ps1
```

Jika berhasil, awal baris terminal menampilkan `(.venv)`.

## 6. Instal dependency

Pastikan `(.venv)` terlihat, kemudian:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Periksa package utama:

```powershell
python -c "import MetaTrader5, pandas, sklearn, joblib; print('Dependency OK')"
```

Jika berhasil, terminal menampilkan `Dependency OK`.

## 7. Sesuaikan simbol

Buka `config.py` menggunakan Notepad:

```powershell
notepad config.py
```

Cari:

```python
SYMBOL = "XAUUSD.vx"
```

Ganti nilainya hanya jika nama simbol emas broker berbeda. Huruf, titik, dan
akhiran harus sama persis dengan Market Watch. Simpan lalu tutup Notepad.

## 8. Konfigurasi akun MT5

Cara paling sederhana adalah membiarkan MT5 terbuka dan sudah login pada akun
yang benar. Bot akan menggunakan sesi terminal tersebut.

Untuk menyimpan konfigurasi akun secara permanen, ganti seluruh placeholder:

```powershell
[Environment]::SetEnvironmentVariable("TRADING_MT5_LOGIN", "NOMOR_LOGIN", "User")
[Environment]::SetEnvironmentVariable("TRADING_MT5_PASSWORD", "PASSWORD_MT5", "User")
[Environment]::SetEnvironmentVariable("TRADING_MT5_SERVER", "NAMA_SERVER", "User")
[Environment]::SetEnvironmentVariable(
    "TRADING_MT5_PATH",
    "C:\Program Files\MetaTrader 5\terminal64.exe",
    "User"
)
```

Path terminal dapat berbeda jika MT5 dipasang oleh broker. Untuk menemukannya:

1. Klik kanan shortcut MT5.
2. Pilih **Properties**.
3. Salin nilai **Target** tanpa tanda kutip.

Setelah menyimpan environment variable, tutup seluruh PowerShell dan buka
PowerShell baru:

```powershell
cd C:\trading
.\.venv\Scripts\Activate.ps1
```

Jangan memakai perintah yang mencetak password ke layar.

## 9. Uji koneksi MT5

Pastikan MT5 terbuka, login, dan Algo Trading aktif:

```powershell
python test_connection.py
```

Jika simbol tidak ditemukan, periksa kembali `SYMBOL` di `config.py` dan
pastikan simbol ditampilkan di Market Watch.

## 10. Pasang notifikasi Telegram

Ikuti [TELEGRAM_SETUP.md](TELEGRAM_SETUP.md) mulai dari pembuatan bot,
mendapatkan Chat ID, menyimpan token permanen, sampai tes pesan.

Telegram bersifat opsional. Bot tetap dapat berjalan tanpa Telegram.

## 11. Jalankan pemeriksaan project

```powershell
python -m unittest discover -s tests -v
```

Semua test harus menampilkan `OK`. Jangan menjalankan bot jika ada `FAILED`
atau `ERROR`.

## 12. Jalankan bot

```powershell
python main.py
```

Contoh awal yang normal:

```text
[mt5_connector] Koneksi ke MT5 berhasil.
Sinyal: none - Belum ada setup valid
```

`Sinyal: none` bukan error. Bot sedang menunggu chart memenuhi syarat.

Hentikan dengan:

```text
Ctrl+C
```

Jangan menjalankan `python main.py` dari dua terminal. Project memiliki
single-instance lock, tetapi pengguna tetap harus menjalankannya satu kali.

## 13. Memahami alasan bot tidak entry

Terminal menjelaskan penyebabnya. Contoh normal:

- Belum ada setup chart valid.
- Spread terlalu tinggi.
- Volatilitas tidak sesuai.
- Masih cooldown progresif.
- Posisi atau risiko terbuka sudah penuh.
- Lot minimum broker melampaui batas risiko.
- Kalender berita atau blackout manual aktif.
- Performa rolling sedang masuk mode probe.
- Drawdown mencapai batas keselamatan.

Cooldown M1 yang digunakan:

- Setelah profit: tanpa jeda.
- Loss pertama: 60 detik.
- Loss kedua berturut-turut: 3 menit.
- Loss ketiga dan seterusnya: 10 menit.
- Loss eksekusi abnormal: 10 menit.

Ketika performa rolling melemah, bot berhenti 10 menit lalu masuk **mode
probe**. Dalam mode ini threshold entry lebih tinggi dan target risiko
dipotong. Bot tidak terkunci selamanya.

## 14. File data lokal

Bot membuat file berikut secara otomatis:

- `trade_log.csv`: data entry.
- `closed_trade_log.csv`: hasil transaksi tertutup.
- `system_log.csv`: aktivitas dan error.
- `shadow_signal_log.csv`: simulasi sinyal AI yang diterima dan ditolak.
- `runtime_state.json`: baseline drawdown dan state proteksi.
- `ml_model.joblib`: model aktif setelah training berhasil.

File tersebut tidak ikut terunduh pada instalasi baru. AI instalasi baru mulai
belajar dari nol berdasarkan akun dan broker pengguna tersebut.

## 15. Pembelajaran AI

Periksa kualitas data:

```powershell
python data_quality.py
```

Pesan berikut normal apabila transaksi belum cukup:

```text
INVALID {'reason': 'baru N trade valid'}
```

Training baru dapat dijalankan setelah minimal 50 closed trade valid:

```powershell
python retrain_model.py
```

Untuk evaluasi yang lebih layak, kumpulkan 200--500 transaksi dari berbagai
kondisi pasar. Kandidat model dapat ditolak apabila hasil out-of-sample buruk;
itu adalah proteksi, bukan kerusakan program.

Lihat laporan:

```powershell
python performance_report.py
```

## 16. Blackout berita opsional

Untuk memasukkan jam berita secara sementara:

```powershell
$env:TRADING_NEWS_BLACKOUT_WINDOWS="13:25-13:40,19:55-20:15"
```

Jam mengikuti waktu komputer. Untuk menyimpannya:

```powershell
[Environment]::SetEnvironmentVariable(
    "TRADING_NEWS_BLACKOUT_WINDOWS",
    "13:25-13:40,19:55-20:15",
    "User"
)
```

Kalender API otomatis hanya bekerja jika endpoint yang digunakan tersedia pada
paket provider Anda. Jangan mengunggah API key ke GitHub.

## 17. Update project dari GitHub

Hentikan bot dengan `Ctrl+C`, lalu:

```powershell
cd C:\trading
.\.venv\Scripts\Activate.ps1
git status
git pull
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

Jika `git pull` menolak karena ada perubahan lokal, jangan gunakan
`git reset --hard`. Simpan perubahan atau minta bantuan untuk menggabungkannya.

## Troubleshooting

### `python` tidak dikenali

Instal ulang Python dan centang **Add python.exe to PATH**, lalu buka
PowerShell baru.

### `ModuleNotFoundError`

Aktifkan virtual environment:

```powershell
cd C:\trading
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### Aktivasi `.venv` ditolak

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Kemudian buka PowerShell baru.

### Koneksi MT5 gagal

- Pastikan MT5 terbuka dan login.
- Pastikan koneksi internet aktif.
- Aktifkan Algo Trading.
- Periksa server, login, path terminal, dan nama simbol.
- Gunakan akun demo dari terminal broker yang sama.

### `Order plan ditolak` atau `lot minimum`

Modal mungkin terlalu kecil dibanding ukuran lot minimum dan jarak SL.
Proteksi ini mencegah risiko aktual melebihi batas. Jangan menaikkan batas
risiko hanya untuk memaksa order.

### Bot berhenti karena drawdown

Baseline drawdown harian tersimpan di `runtime_state.json` dan tidak ter-reset
hanya dengan restart. Jangan menghapus state untuk menghindari proteksi.

### Menjalankan tanpa aktivasi `.venv`

Gunakan interpreter lengkap:

```powershell
C:\trading\.venv\Scripts\python.exe C:\trading\main.py
```
