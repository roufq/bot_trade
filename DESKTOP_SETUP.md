# Aplikasi Desktop AI Trading

Aplikasi desktop menyediakan form konfigurasi dan tombol kontrol sehingga
pengguna tidak perlu menjalankan perintah trading melalui PowerShell setiap
hari. MetaTrader 5 tetap harus terpasang, terbuka, dan login.

## Fitur

- Dashboard gelap modern dengan kartu closed trade, win rate, net profit, dan
  status model AI.
- Status engine berwarna dan tombol Start/Stop yang mudah dibedakan.
- Konfigurasi dikelompokkan menjadi Trading & Risk, MetaTrader 5, serta
  Notifikasi & Berita.
- Live Log bertema terminal dengan lokasi data yang selalu terlihat.
- Start dan Stop engine trading.
- Log terminal langsung di dalam aplikasi.
- Konfigurasi simbol, risiko, drawdown, spread, MT5, Telegram, dan blackout.
- Konfigurasi maksimum posisi total dan maksimum posisi untuk satu arah.
- Penyimpanan konfigurasi pada environment variable pengguna Windows.
- Password dan token ditampilkan sebagai field tertutup dan tidak ditulis ke
  repository.
- Tes koneksi MT5 dan Telegram.
- Audit data, training AI, laporan performa, dan self-check.
- Ringkasan jumlah closed trade, win rate, net profit, dan status model.

## Menjalankan dari source code

Selesaikan [INSTALLATION.md](INSTALLATION.md), lalu:

```powershell
cd C:\trading
.\.venv\Scripts\Activate.ps1
python desktop_app.py
```

Jangan menjalankan `main.py` secara terpisah ketika ingin memakai tombol Start
di aplikasi desktop. Single-instance lock akan menolak engine kedua.

## Pemakaian pertama

1. Buka tab **Konfigurasi**.
2. Isi nama simbol broker.
3. Isi konfigurasi MT5 atau biarkan kosong jika terminal sudah login.
4. Isi Telegram bila notifikasi dibutuhkan.
5. Klik **Simpan Konfigurasi**.
6. Buka MT5 dan aktifkan **Algo Trading**.
7. Kembali ke Dashboard dan jalankan **Tes MT5**.
8. Jalankan **Tes Telegram**.
9. Klik **Start Bot**.
10. Pantau tab **Log**.

Setelah konfigurasi diubah, Stop lalu Start engine agar module Python membaca
nilai baru.

## Membuat file EXE

Build harus dilakukan pada Windows:

```powershell
cd C:\trading
.\.venv\Scripts\Activate.ps1
.\build_desktop.ps1
```

Skrip akan:

1. Memasang dependency desktop dan PyInstaller.
2. Menjalankan seluruh test.
3. Membuat aplikasi one-file.

Hasilnya:

```text
C:\trading\AITradingDesktop.exe
```

Versi di root project menggunakan histori CSV, model, dan runtime state yang
sudah ada. Jangan menjalankan salinan di `dist` untuk akun yang sedang belajar,
karena folder kerja dan datanya berbeda.

Untuk instalasi baru di komputer lain, salin EXE ke folder khusus yang dapat
ditulis, misalnya:

```text
C:\AITradingDesktop\
```

Log CSV, model, lock, dan runtime state akan dibuat di folder EXE. Jangan
menjalankan EXE langsung dari ZIP atau folder read-only.

## Instalasi di komputer lain

Komputer tujuan tetap memerlukan:

1. Windows 10/11 64-bit.
2. MetaTrader 5 dari broker.
3. Akun demo yang sudah login.
4. Algo Trading aktif.

Python tidak diperlukan pada komputer tujuan jika memakai EXE hasil build.

Untuk pengguna awam, distribusikan installer berikut, bukan folder source:

```text
installer_output\AITradingDesktop-Setup-1.3.0.exe
```

Langkah pengguna:

1. Tutup versi aplikasi yang lama jika sedang berjalan.
2. Jalankan `AITradingDesktop-Setup-1.3.0.exe`.
3. Ikuti wizard dan pilih shortcut Desktop bila diinginkan.
4. Buka **AI Trading Desktop** dari Start Menu atau Desktop.
5. Isi tab **Konfigurasi**.
6. Buka MT5, login akun demo, dan aktifkan Algo Trading.
7. Jalankan Tes MT5 dan klik Start Bot.

Installer tidak memerlukan Python dan tidak memerlukan hak Administrator.
Program dipasang ke:

```text
%LOCALAPPDATA%\Programs\AITradingDesktop
```

Data pengguna disimpan terpisah:

```text
%LOCALAPPDATA%\AITradingDesktop\Data
```

Folder data berisi CSV, model, log, dan runtime state. Upgrade aplikasi dengan
installer versi lebih baru memakai `AppId` yang sama sehingga data tidak
ditimpa. Uninstall juga tidak menghapus data trading secara otomatis.

Jika pengguna ingin menghapus seluruh data setelah uninstall, hapus manual:

```powershell
Remove-Item -LiteralPath "$env:LOCALAPPDATA\AITradingDesktop" -Recurse
```

Pastikan tidak ada histori atau model yang masih dibutuhkan sebelum menjalankan
perintah tersebut.

Pada pemakaian pertama Windows Defender dapat memeriksa file cukup lama.
PyInstaller EXE yang belum ditandatangani juga dapat menampilkan SmartScreen.
Distribusi publik sebaiknya menggunakan code-signing certificate; jangan
menyuruh pengguna mematikan antivirus.

File installer saat ini belum ditandatangani secara digital. SmartScreen dapat
menampilkan nama publisher yang tidak dikenal. Code signing memerlukan
sertifikat resmi atas nama publisher dan tidak dapat digantikan dengan sekadar
mengubah source code.

## Update aplikasi

1. Naikkan `APP_VERSION` di `desktop_app.py`.
2. Sesuaikan versi di `version_info.txt` dan `installer.iss`.
3. Tutup aplikasi desktop dan engine.
4. Jalankan `build_desktop.ps1`.
5. Distribusikan Setup versi baru.

Pengguna cukup menjalankan installer versi baru. Konfigurasi environment dan
folder data tetap dipertahankan.

## Aturan jumlah posisi

Tab Konfigurasi menyediakan:

- Profil awal Konservatif, Seimbang, dan Aktif.
- Pengaturan manual strategi A/B, FVG H1/M15 dengan trigger M1, EMA, RSI, ATR,
  SL/TP, jarak entry, volatilitas, jam trading,
  break-even, dan trailing stop.
- Validasi hubungan antarnilai sebelum konfigurasi dapat disimpan.

- **Maks posisi terbuka total**: jumlah seluruh posisi aktif pada simbol.
- **Maks posisi untuk satu arah**: batas posisi BUY saja atau SELL saja.

Nilai bawaan adalah 3 posisi total dan 2 posisi per arah. Contohnya, konfigurasi
tersebut dapat menampung 2 BUY dan 1 SELL, tetapi tidak dapat menampung 3 BUY.

Bot tetap hanya membuat maksimal satu order baru pada satu candle yang sudah
tertutup. Jika setup masih valid pada candle berikutnya, posisi dapat bertambah
sampai batas. Bot juga menolak penambahan posisi searah apabila posisi searah
yang ada sedang mengalami floating loss.

Pengaturan ini adalah batas exposure, bukan perintah agar bot selalu membuka
beberapa posisi. Slot tambahan hanya digunakan jika chart, spread, risiko,
jarak entry, dan filter lain memenuhi syarat.

## Keamanan

- Jangan membagikan EXE bersama CSV akun atau `runtime_state.json`.
- Jangan memasukkan token atau password ke source code sebelum build.
- Environment variable Windows bukan brankas terenkripsi. Untuk komputer
  bersama, gunakan akun Windows terpisah dan batasi akses.
- Uji pada akun demo sebelum akun live.
- GUI tidak menjamin profit dan tidak mengubah risiko pasar.

## Stop engine

Tombol Stop membuat sinyal penghentian lokal. Engine menyelesaikan siklus,
mencatat shutdown, mengirim notifikasi Telegram, lalu disconnect dari MT5.
Jika engine tidak merespons dalam batas waktu, aplikasi menggunakan terminasi
proses sebagai fallback.

Menutup GUI ketika engine aktif akan meminta konfirmasi.

## Troubleshooting

### Tombol Start langsung kembali berhenti

- Lihat tab Log.
- Pastikan tidak ada `main.py` atau EXE lain yang masih menjalankan engine.
- Periksa MT5, login, simbol, dan Algo Trading.

### Tes MT5 gagal

- Buka terminal MT5 dari broker.
- Login ke akun demo.
- Pastikan path dan server benar.
- Pastikan simbol sama persis dengan Market Watch.

### Build gagal pada PyInstaller

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements-desktop.txt
.\build_desktop.ps1
```

Periksa bahwa build dijalankan dari PowerShell Windows dan `.venv` aktif.

### EXE tidak dapat menulis log

Pindahkan EXE dari `Program Files`, ZIP, atau folder read-only ke folder seperti
`C:\AITradingDesktop`.
