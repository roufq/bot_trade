# Panduan Telegram Bot Trading untuk Pemula

Panduan ini dimulai dari membuat akun Telegram sampai notifikasi bot trading
berhasil masuk. Konfigurasi menggunakan environment variable agar token tidak
tersimpan di source code atau GitHub.

## Yang dibutuhkan

- Aplikasi Telegram di ponsel atau komputer.
- Project sudah dipasang mengikuti [INSTALLATION.md](INSTALLATION.md).
- PowerShell.
- Koneksi internet.

## 1. Buat bot melalui BotFather

1. Buka Telegram.
2. Cari `@BotFather`.
3. Pastikan akun memiliki tanda verifikasi Telegram.
4. Tekan **Start**.
5. Kirim:

```text
/newbot
```

6. Masukkan nama bebas, misalnya `Notifikasi Trading Saya`.
7. Masukkan username unik yang berakhiran `bot`, misalnya
   `notifikasi_trading_saya_bot`.
8. BotFather memberikan token berbentuk:

```text
1234567890:CONTOH_TOKEN_RAHASIA
```

Token adalah password bot. Jangan kirim token ke orang lain, screenshot,
GitHub, issue, atau grup.

## 2. Mulai chat dengan bot

Bot tidak dapat mengirim pesan pribadi sebelum Anda memulai percakapan:

1. Tekan link bot yang diberikan BotFather.
2. Tekan **Start**.
3. Kirim `/start`.
4. Kirim satu pesan biasa, misalnya `Halo`.

## 3. Dapatkan Chat ID

Buka browser dan ganti `<TOKEN>` dengan token milik Anda:

```text
https://api.telegram.org/bot<TOKEN>/getUpdates
```

Contoh struktur hasil:

```json
{
  "ok": true,
  "result": [
    {
      "update_id": 987654,
      "message": {
        "message_id": 25,
        "chat": {
          "id": 123456789,
          "type": "private"
        }
      }
    }
  ]
}
```

Gunakan angka pada:

```text
message → chat → id
```

Pada contoh, Chat ID adalah `123456789`.

Jangan memakai:

- `message_id`
- `update_id`
- username Telegram

Jika `"result":[]`:

1. Pastikan Anda membuka bot yang sama dengan token tersebut.
2. Tekan **Start**.
3. Kirim pesan baru kepada bot.
4. Refresh halaman `getUpdates`.

Jika masih kosong, buka:

```text
https://api.telegram.org/bot<TOKEN>/deleteWebhook
```

Kemudian kirim pesan baru dan buka `getUpdates` kembali.

## 4. Chat ID grup opsional

Untuk mengirim notifikasi ke grup:

1. Tambahkan bot ke grup.
2. Kirim pesan di grup, misalnya `/start@username_bot`.
3. Buka `getUpdates`.
4. Cari `message.chat.id`.

Chat ID grup biasanya negatif, misalnya:

```text
-1001234567890
```

Tanda minus wajib ikut disimpan. Pastikan bot mempunyai izin mengirim pesan.

## 5. Simpan token dan Chat ID sementara

Buka PowerShell:

```powershell
cd C:\trading
.\.venv\Scripts\Activate.ps1
```

Ganti placeholder:

```powershell
$env:TRADING_TELEGRAM_BOT_TOKEN="TOKEN_BARU_ANDA"
$env:TRADING_TELEGRAM_CHAT_ID="CHAT_ID_ANDA"
```

Konfigurasi ini hilang ketika PowerShell ditutup.

Periksa tanpa mencetak token:

```powershell
Write-Host "Token tersedia:" ([bool]$env:TRADING_TELEGRAM_BOT_TOKEN)
Write-Host "Chat ID tersedia:" ([bool]$env:TRADING_TELEGRAM_CHAT_ID)
python -c "import config; print('Telegram aktif:', config.TELEGRAM_ENABLED)"
```

Ketiganya harus menghasilkan `True`.

## 6. Tes pengiriman pesan

```powershell
python -c "import notifier; print(notifier.send_telegram_message('Tes notifikasi trading'))"
```

Jika berhasil:

- Pesan masuk ke Telegram.
- Terminal menampilkan `True`.

Jangan lanjut ke konfigurasi permanen sebelum tes sementara berhasil.

## 7. Simpan konfigurasi permanen

Jalankan satu per satu dan ganti placeholder:

```powershell
[Environment]::SetEnvironmentVariable(
    "TRADING_TELEGRAM_BOT_TOKEN",
    "TOKEN_BARU_ANDA",
    "User"
)
```

```powershell
[Environment]::SetEnvironmentVariable(
    "TRADING_TELEGRAM_CHAT_ID",
    "CHAT_ID_ANDA",
    "User"
)
```

Environment variable permanen tidak masuk ke PowerShell yang sudah terbuka.
Lakukan:

1. Tutup seluruh jendela PowerShell.
2. Buka PowerShell baru.
3. Aktifkan project:

```powershell
cd C:\trading
.\.venv\Scripts\Activate.ps1
```

4. Periksa:

```powershell
Write-Host "Token tersedia:" ([bool]$env:TRADING_TELEGRAM_BOT_TOKEN)
Write-Host "Chat ID tersedia:" ([bool]$env:TRADING_TELEGRAM_CHAT_ID)
python -c "import config; print('Telegram aktif:', config.TELEGRAM_ENABLED)"
```

5. Tes lagi:

```powershell
python -c "import notifier; print(notifier.send_telegram_message('Tes konfigurasi permanen'))"
```

## 8. Jalankan bot trading

Pastikan MT5 terbuka dan sudah login:

```powershell
python main.py
```

Bot dapat mengirim notifikasi ketika:

- Bot berhasil dimulai.
- Order berhasil dibuka.
- Posisi ditutup beserta profit atau loss.
- Error penting terjadi.
- Drawdown harian mencapai batas.
- Bot dihentikan secara normal dengan `Ctrl+C`.

Notifikasi start baru dikirim setelah koneksi MT5 berhasil. Jika koneksi MT5
gagal, pesan start tidak akan dikirim.

## 9. Tes API Telegram secara aman

Untuk memeriksa identitas bot, buka:

```text
https://api.telegram.org/bot<TOKEN>/getMe
```

Jangan membagikan URL lengkap karena token berada di dalam URL.

Untuk menguji lewat PowerShell tanpa menampilkan token:

```powershell
$telegramUrl = "https://api.telegram.org/bot$env:TRADING_TELEGRAM_BOT_TOKEN/getMe"
Invoke-RestMethod -Uri $telegramUrl
```

## Troubleshooting

### `Telegram aktif: False`

Periksa nama variabel. Harus persis:

```text
TRADING_TELEGRAM_BOT_TOKEN
TRADING_TELEGRAM_CHAT_ID
```

Periksa:

```powershell
Write-Host ([bool]$env:TRADING_TELEGRAM_BOT_TOKEN)
Write-Host ([bool]$env:TRADING_TELEGRAM_CHAT_ID)
```

Jika konfigurasi baru saja disimpan permanen, tutup dan buka PowerShell baru.

### `Bad Request: chat not found`

Penyebab umum:

- Menggunakan `message_id`, bukan `message.chat.id`.
- Belum menekan **Start**.
- Token berasal dari bot lain.
- Chat ID grup kehilangan tanda minus.
- Bot sudah dikeluarkan dari grup.

Ulangi langkah 2 dan 3 menggunakan bot yang sama.

### `"result":[]`

- Kirim pesan baru kepada bot.
- Pastikan token sesuai dengan bot tersebut.
- Refresh `getUpdates`.
- Hapus webhook menggunakan `deleteWebhook`, lalu kirim pesan lagi.

### `Unauthorized` atau HTTP 401

Token salah, sudah dicabut, atau memiliki spasi tambahan. Buat token baru
melalui BotFather dan simpan ulang.

### HTTP 400

Baca detail setelah `Bad Request`. Penyebab paling umum adalah Chat ID salah.
Tes `getMe` untuk memastikan token valid, lalu ambil ulang `message.chat.id`.

### Tes pesan berhasil, tetapi start bot tidak mengirim pesan

1. Pastikan perintah `python main.py` dijalankan dari PowerShell yang memiliki
   environment variable.
2. Periksa `TELEGRAM_ENABLED`.
3. Pastikan MT5 berhasil terkoneksi.
4. Pastikan hanya satu instance bot berjalan.
5. Periksa `system_log.csv`.

### Pesan stop tidak masuk

Hentikan bot dengan `Ctrl+C`. Menutup PowerShell secara paksa, mematikan
komputer, atau menghentikan proses dari Task Manager tidak memberi bot waktu
untuk mengirim pesan stop.

### Token pernah terlihat atau dibagikan

Token tersebut harus dianggap bocor:

1. Buka `@BotFather`.
2. Kirim `/revoke`.
3. Pilih bot.
4. Buat token baru dengan `/token` bila diperlukan.
5. Simpan token baru sebagai environment variable.
6. Tutup dan buka PowerShell.
7. Tes ulang.

Jangan menggunakan kembali token lama.

## Mengganti token permanen

```powershell
[Environment]::SetEnvironmentVariable(
    "TRADING_TELEGRAM_BOT_TOKEN",
    "TOKEN_BARU_ANDA",
    "User"
)
```

Tutup PowerShell, buka kembali, lalu tes.

## Menghapus konfigurasi Telegram

Jika Telegram tidak ingin digunakan:

```powershell
[Environment]::SetEnvironmentVariable("TRADING_TELEGRAM_BOT_TOKEN", $null, "User")
[Environment]::SetEnvironmentVariable("TRADING_TELEGRAM_CHAT_ID", $null, "User")
```

Tutup dan buka PowerShell baru. Bot trading tetap berjalan tanpa notifikasi
Telegram.
