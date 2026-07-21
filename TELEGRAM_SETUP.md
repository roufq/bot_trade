# Instalasi Notifikasi Telegram

Panduan ini menjelaskan cara menghubungkan bot trading dengan Telegram di
Windows PowerShell. Jangan menyimpan atau membagikan token asli di source code,
screenshot, GitHub, atau percakapan.

## 1. Membuat bot Telegram

1. Buka Telegram dan cari akun resmi `@BotFather`.
2. Kirim perintah `/newbot`.
3. Isi nama dan username bot sesuai petunjuk. Username harus berakhiran `bot`.
4. Simpan token yang diberikan BotFather di tempat aman.

Jika token pernah tersebar, kirim `/revoke` ke BotFather dan buat token baru
dengan `/token`.

## 2. Memulai percakapan dengan bot

1. Buka alamat `https://t.me/USERNAME_BOT` sesuai username bot Anda.
2. Tekan **Start**.
3. Kirim pesan `/start`, lalu kirim pesan biasa seperti `Halo`.

Bot tidak dapat mengirim pesan pribadi sebelum pengguna memulai percakapan.

## 3. Mendapatkan Chat ID

Buka alamat berikut di browser dengan mengganti `<TOKEN>` memakai token bot:

```text
https://api.telegram.org/bot<TOKEN>/getUpdates
```

Cari bagian berikut:

```json
{
  "message": {
    "message_id": 123,
    "chat": {
      "id": 123456789,
      "type": "private"
    }
  }
}
```

Gunakan nilai `message.chat.id`. Jangan menggunakan `message_id` atau
`update_id`. Chat ID grup biasanya berupa angka negatif dan tanda minusnya
wajib disertakan.

Jika `result` masih kosong:

1. Pastikan pesan dikirim kepada bot yang tokennya sedang digunakan.
2. Tekan **Start** dan kirim pesan baru.
3. Refresh halaman `getUpdates`.
4. Jika tetap kosong, buka
   `https://api.telegram.org/bot<TOKEN>/deleteWebhook`, kirim pesan baru, lalu
   buka kembali `getUpdates`.

## 4. Konfigurasi sementara

Konfigurasi ini hanya berlaku pada jendela PowerShell yang sedang dibuka:

```powershell
$env:TRADING_TELEGRAM_BOT_TOKEN="TOKEN_BARU_ANDA"
$env:TRADING_TELEGRAM_CHAT_ID="CHAT_ID_ANDA"
```

Aktifkan virtual environment dan periksa konfigurasi:

```powershell
cd C:\trading
.\.venv\Scripts\Activate.ps1
python -c "import config; print(config.TELEGRAM_ENABLED)"
```

Hasilnya harus `True`.

## 5. Menyimpan konfigurasi permanen

Jalankan di PowerShell:

```powershell
[Environment]::SetEnvironmentVariable(
    "TRADING_TELEGRAM_BOT_TOKEN",
    "TOKEN_BARU_ANDA",
    "User"
)

[Environment]::SetEnvironmentVariable(
    "TRADING_TELEGRAM_CHAT_ID",
    "CHAT_ID_ANDA",
    "User"
)
```

Tutup seluruh PowerShell, buka terminal baru, lalu aktifkan `.venv` kembali.
Environment variable permanen tidak otomatis muncul pada terminal yang sudah
terbuka sebelum variabel tersebut dibuat.

## 6. Menguji notifikasi

```powershell
python -c "import notifier; print(notifier.send_telegram_message('Tes notifikasi trading'))"
```

Jika berhasil, pesan masuk ke Telegram dan terminal menampilkan `True`.

Setelah itu jalankan bot dari terminal yang sama:

```powershell
python main.py
```

Bot mengirim notifikasi ketika koneksi MT5 berhasil, order dibuka, posisi
ditutup, terjadi error tertentu, drawdown harian tercapai, dan bot dihentikan
dengan `Ctrl+C`.

## 7. Troubleshooting

### `TELEGRAM_ENABLED` menghasilkan `False`

Periksa keberadaan variabel tanpa mencetak token:

```powershell
Write-Host "Token tersedia:" ([bool]$env:TRADING_TELEGRAM_BOT_TOKEN)
Write-Host "Chat ID tersedia:" ([bool]$env:TRADING_TELEGRAM_CHAT_ID)
```

Keduanya harus menghasilkan `True`. Jangan mengganti nama environment variable
di dalam `config.py`.

### `Bad Request: chat not found`

- Pastikan yang dipakai adalah `message.chat.id`.
- Pastikan Anda sudah menekan **Start** pada bot yang benar.
- Pastikan token dan Chat ID berasal dari bot/percakapan yang sama.
- Untuk grup, sertakan tanda minus pada Chat ID.

### Tes berhasil tetapi restart tidak mengirim pesan

- Simpan variabel secara permanen seperti langkah 5.
- Buka PowerShell baru setelah menyimpan variabel.
- Pastikan `TELEGRAM_ENABLED` bernilai `True`.
- Notifikasi start baru dikirim setelah koneksi MT5 berhasil.
- Hentikan bot dengan `Ctrl+C`; menutup terminal secara paksa tidak menjamin
  notifikasi stop terkirim.

### Token terlihat pada terminal atau screenshot

Segera kirim `/revoke` kepada `@BotFather`, buat token baru, lalu perbarui
`TRADING_TELEGRAM_BOT_TOKEN`. Token yang sudah tersebar tidak boleh digunakan
kembali.
