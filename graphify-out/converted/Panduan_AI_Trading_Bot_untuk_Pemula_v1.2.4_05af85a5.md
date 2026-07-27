<!-- converted from Panduan_AI_Trading_Bot_untuk_Pemula_v1.2.4.docx -->

Panduan Lengkap
AI Trading Bot untuk Pemula
Versi Desktop 1.2.4
Penjelasan sederhana dari dasar sampai seluruh pengaturan

Dokumen proyek • 23 Juli 2026

Dokumen ini dibuat agar orang yang belum pernah mengenal trading, pemrograman,
atau kecerdasan buatan tetap dapat memahami dan memakai aplikasi.
Versi aplikasi yang dijelaskan: AI Trading Desktop 1.2.4.
Penting: bot tidak dapat menjamin keuntungan dan tidak dapat menghilangkan
kerugian. Gunakan akun latihan atau akun demo terlebih dahulu. Jangan memakai
uang kebutuhan sehari-hari untuk trading.
# 1. Apa itu AI Trading Bot?
AI Trading Bot adalah program yang membantu membuka dan mengelola transaksi
secara otomatis di aplikasi MetaTrader 5.
Bot melakukan pekerjaan berikut:
- membaca perubahan harga emas;
- mencari arah harga yang sedang lebih kuat;
- mencari waktu masuk yang dinilai cukup aman;
- menentukan ukuran transaksi;
- memasang batas rugi dan target keuntungan;
- mengawasi transaksi yang masih terbuka;
- mencatat hasil untung maupun rugi;
- memakai catatan tersebut untuk menyesuaikan keputusan berikutnya.
AI adalah singkatan dari Artificial Intelligence, dalam bahasa Indonesia
berarti kecerdasan buatan. Pada proyek ini, AI bukan peramal harga. AI hanya
mengolah pola dan pengalaman sebelumnya untuk membantu menilai peluang.
# 2. Istilah dasar yang harus dipahami
## Trading
Trading adalah kegiatan membeli atau menjual suatu barang keuangan dengan tujuan
mendapatkan keuntungan dari perubahan harga.
## BUY
BUY berarti membuka transaksi dengan perkiraan harga akan naik. BUY memperoleh
keuntungan jika harga naik setelah transaksi dibuka.
## SELL
SELL berarti membuka transaksi dengan perkiraan harga akan turun. SELL memperoleh
keuntungan jika harga turun setelah transaksi dibuka.
Bot memperlakukan BUY dan SELL secara seimbang. Bot tidak melarang SELL hanya
karena transaksi SELL sebelumnya rugi, dan tidak selalu memilih BUY hanya karena
riwayat BUY sebelumnya lebih bagus.
## Entry atau OP
Entry berarti membuka transaksi. Sebagian trader menyebutnya OP, singkatan dari
Open Position atau membuka posisi.
## Close
Close berarti menutup transaksi. Setelah ditutup, hasil untung atau rugi menjadi
hasil nyata dan dimasukkan ke riwayat bot.
## Profit dan loss
Profit berarti keuntungan. Loss berarti kerugian. Pada log bot:
profit=+4.13
berarti untung 4,13 dalam mata uang akun. Contoh:
profit=-2.18
berarti rugi 2,18.
## Balance dan equity
Balance adalah saldo setelah semua transaksi yang sudah ditutup dihitung.
Equity adalah nilai akun saat ini setelah keuntungan atau kerugian dari transaksi
yang masih terbuka ikut diperhitungkan.
## Lot
Lot adalah ukuran transaksi. Lot lebih besar dapat menghasilkan untung lebih
besar, tetapi kerugiannya juga lebih besar. Bot menghitung lot berdasarkan saldo,
jarak batas rugi, dan aturan broker.
## Broker
Broker adalah perusahaan yang menyediakan akun dan sambungan ke pasar. Nama
simbol, spread, ukuran lot minimum, dan aturan transaksi dapat berbeda pada
setiap broker.
## XAUUSD
XAU adalah kode untuk emas dan USD adalah kode untuk dolar Amerika Serikat.
XAUUSD berarti harga emas terhadap dolar Amerika. Broker pada proyek ini memakai
nama bawaan XAUUSD.vx, tetapi nama tersebut dapat diubah.
## MT5
MT5 adalah singkatan dari MetaTrader 5, yaitu aplikasi yang digunakan untuk
melihat chart dan mengirim transaksi ke broker.
## Chart dan candle
Chart adalah gambar pergerakan harga. Candle atau candlestick adalah satu batang
harga yang menunjukkan harga pembukaan, harga tertinggi, harga terendah, dan
harga penutupan selama jangka waktu tertentu.
## Timeframe dan M1
Timeframe adalah jangka waktu satu candle. M1 berarti satu candle mewakili satu
menit. Bot saat ini memakai M1 untuk membaca tren dan mencari entry.
## Trend, sideways, pullback, dan momentum
- Trend adalah pergerakan harga yang cenderung menuju satu arah.
- Sideways adalah harga yang bergerak naik-turun dalam area sempit tanpa arah jelas.
- Pullback adalah gerakan sementara yang berlawanan dengan tren sebelum tren mungkin berlanjut.
- Momentum adalah kekuatan gerakan harga pada saat itu.
## Volatilitas
Volatilitas adalah ukuran seberapa besar atau cepat harga bergerak. Volatilitas
terlalu rendah dapat berarti pasar tidak bergerak. Volatilitas terlalu tinggi
dapat membuat harga berubah sangat cepat dan berisiko.
## Spread
Spread adalah selisih antara harga BUY dan SELL yang diberikan broker. Spread
adalah salah satu biaya trading. Spread besar membuat transaksi langsung berada
dalam keadaan rugi lebih besar ketika baru dibuka.
## Point
Point adalah satuan perubahan harga terkecil yang dipakai broker. Karena jumlah
angka di belakang koma berbeda pada setiap broker, 30 points tidak selalu sama
dengan 30 dolar.
## SL dan TP
SL adalah singkatan dari Stop Loss, yaitu batas untuk menutup transaksi agar
kerugian tidak terus membesar.
TP adalah singkatan dari Take Profit, yaitu target untuk menutup transaksi
ketika keuntungan sudah mencapai nilai tertentu.
## Break-even
Break-even berarti memindahkan Stop Loss mendekati harga masuk setelah transaksi
sudah untung. Tujuannya agar transaksi yang sebelumnya untung tidak berubah
menjadi kerugian besar.
## Trailing stop
Trailing stop adalah Stop Loss yang mengikuti harga ketika harga bergerak ke arah
yang menguntungkan. Jika harga berbalik, transaksi dapat ditutup dan sebagian
keuntungan dipertahankan.
## Drawdown
Drawdown adalah penurunan nilai akun dari nilai sebelumnya. Contoh: nilai akun
turun dari 100 menjadi 95, berarti drawdown sekitar 5%.
## Cooldown
Cooldown adalah waktu istirahat sementara setelah kondisi tertentu, misalnya
setelah rugi. Selama cooldown, bot tetap membaca pasar tetapi tidak membuka
transaksi baru.
## Kill-switch
Kill-switch adalah pengaman yang menghentikan entry baru ketika performa atau
kerugian dianggap tidak aman. Pengaman ini tidak berarti program rusak.
## API
API adalah singkatan dari Application Programming Interface. Secara sederhana,
API adalah jalur yang memungkinkan bot meminta data dari layanan lain, misalnya
kalender berita ekonomi.
# 3. Cara bot mengambil keputusan
Bot tidak membuka transaksi hanya karena satu candle terlihat naik atau turun.
Setiap peluang harus melewati beberapa pemeriksaan.
Urutan sederhananya:
- memastikan MT5 tersambung;
- mengambil harga dan candle terbaru;
- memastikan waktu trading diizinkan;
- memastikan kondisi akun masih aman;
- memeriksa spread dan kecepatan pergerakan harga;
- menentukan apakah arah lebih cocok BUY, SELL, atau belum jelas;
- mencari waktu entry;
- menilai pengalaman transaksi sebelumnya;
- menghitung ukuran lot, Stop Loss, dan Take Profit;
- memeriksa aturan broker;
- mengirim order jika semua syarat terpenuhi.
Karena banyak pemeriksaan tersebut, chart yang terlihat memiliki peluang belum
tentu langsung menghasilkan transaksi. Hal ini bertujuan menghindari entry yang
terlambat, biaya terlalu mahal, atau kondisi yang terlalu berisiko.
# 4. Tiga cara bot melakukan entry
## Crossover atau persilangan
Crossover terjadi ketika garis rata-rata harga yang lebih cepat memotong garis
yang lebih lambat. Ini dapat menjadi tanda awal perubahan arah.
## Continuation atau mengikuti tren
Continuation berarti bot mengikuti tren yang sudah berjalan. Bot biasanya
menunggu harga kembali mendekati garis rata-rata harga, lalu mencari tanda bahwa
tren akan berlanjut.
## Momentum
Momentum entry digunakan ketika arah dan kekuatan harga masih sesuai walaupun
tidak ada persilangan baru.
Jadi, bot tidak hanya entry saat pembalikan harga. Bot juga dapat mengikuti tren.
Namun bot menghindari mengejar harga yang sudah melonjak terlalu jauh karena
entry seperti itu lebih mudah terkena pembalikan.
# 5. Indikator yang digunakan
Indikator adalah perhitungan dari data harga. Indikator membantu bot membuat
aturan yang konsisten.
## EMA
EMA adalah singkatan dari Exponential Moving Average, yaitu garis rata-rata
harga yang lebih memperhatikan harga terbaru.
Bot memakai:
- EMA 20 dan EMA 50 untuk melihat arah yang lebih umum;
- EMA 5 dan EMA 13 untuk mencari waktu masuk.
Angka yang lebih kecil membuat garis lebih cepat mengikuti harga. Angka yang
lebih besar membuat garis lebih lambat dan lebih tenang.
## RSI
RSI adalah singkatan dari Relative Strength Index, yaitu angka dari 0 sampai
100 untuk membantu melihat kekuatan gerakan harga.
Secara bawaan:
- BUY memerlukan RSI minimal 55;
- SELL memerlukan RSI maksimal 45.
RSI bukan jaminan harga akan naik atau turun. RSI hanya salah satu syarat.
## ATR
ATR adalah singkatan dari Average True Range, yaitu ukuran rata-rata besar
pergerakan harga. ATR tidak menunjukkan arah. ATR hanya menunjukkan apakah harga
sedang bergerak kecil atau besar.
Bot memakai ATR untuk menentukan:
- jarak Stop Loss;
- jarak Take Profit;
- jarak aman antar-entry;
- apakah spread relatif mahal;
- apakah pasar terlalu sepi atau terlalu cepat.
# 6. Bagaimana AI belajar
Proyek mempunyai dua lapisan pembelajaran.
## Pembelajaran statistik
Pembelajaran statistik melihat:
- berapa transaksi yang untung dan rugi;
- besar rata-rata keuntungan;
- besar rata-rata kerugian;
- jumlah loss berturut-turut;
- penurunan nilai akun;
- hasil dari jenis setup yang mirip;
- kekuatan kondisi pasar saat ini.
Hasilnya disebut learning score atau nilai pembelajaran. Nilai yang lebih tinggi
berarti kondisi dinilai lebih mendukung. Nilai rendah membuat risiko diperkecil
atau entry ditolak.
## Model machine learning
Machine learning berarti program mencari hubungan dari banyak contoh transaksi.
Model baru dilatih setelah terdapat sedikitnya 50 transaksi tertutup yang valid
dan hasilnya bervariasi.
Jika log menampilkan:
AI model belum tersedia atau tidak dapat memprediksi.
bot tetap dapat bekerja memakai aturan strategi dan pembelajaran statistik.
Pesan tersebut tidak selalu berarti ada kerusakan.
Model mempelajari keadaan pasar saat entry, bukan sekadar menghafal bahwa BUY
lebih baik daripada SELL. Model juga harus lulus pemeriksaan kualitas sebelum
dipakai.
# 7. Penjelasan skor pada log
Contoh:
Learning score=0.50, combined_score=0.50, risk=0.25%
Entry ditolak: combined score 0.50 di bawah threshold 0.65
Artinya:
- learning score adalah penilaian dari pengalaman dan keadaan pasar;
- combined score adalah nilai akhir setelah digabung dengan AI jika model tersedia;
- risk 0,25% adalah bagian akun yang direncanakan berisiko;
- threshold adalah nilai minimum agar entry diizinkan.
Dalam contoh tersebut, nilai akhir 0,50 lebih kecil daripada syarat minimum 0,65,
sehingga tidak ada order.
# 8. Pengaturan desktop: panduan lengkap
Bagian ini menjelaskan seluruh pengaturan yang terlihat pada tab Konfigurasi.
Nilai default adalah nilai awal aplikasi. Setelah mengubah pengaturan, klik
Simpan Konfigurasi, lalu Stop dan Start bot agar perubahan digunakan.
Versi 1.2.4 mempunyai 43 pengaturan.
## 8.0 Folder data terpadu
Fungsi: menentukan satu folder yang dipakai bersama untuk menyimpan pengalaman
entry, closed trade, shadow signal, model AI, dan status pengaman. Source project
dan aplikasi desktop harus menunjuk ke folder yang sama agar tidak mempunyai
pengalaman berbeda.
Gunakan tombol Import CSV Pengalaman untuk menggabungkan data lama. Data
digabung berdasarkan ticket sehingga transaksi yang sama tidak dihitung dua
kali. Aplikasi membuat backup sebelum memperbarui histori. Tombol Export CSV Pengalaman
menyalin tiga CSV pengalaman ke folder bertanggal dan tidak menyertakan password,
token, atau pengaturan rahasia.
## 8.1 Symbol broker
Nilai default: XAUUSD.vx.
Fungsi: menentukan barang yang diperdagangkan. Isi harus sama persis dengan nama
yang muncul pada Market Watch MT5. Jika broker memakai XAUUSD, jangan memakai
XAUUSD.vx.
Jika salah: bot tidak dapat mengambil harga atau mengirim order.
## 8.2 Risiko per trade (%)
Nilai default: 0.50.
Fungsi: menentukan target persentase nilai akun yang boleh berisiko pada satu
transaksi. Contoh 0,50% dari equity 300 adalah sekitar 1,50.
Jika dinaikkan: potensi keuntungan dan kerugian per transaksi membesar.
Jika diturunkan: perubahan saldo menjadi lebih kecil dan akun lebih tahan
terhadap rangkaian loss.
Rentang aplikasi: 0,01% sampai 2%. Hard safety tetap membatasi risiko aktual.
## 8.3 Max drawdown harian (%)
Nilai default: 5.0.
Fungsi: menghentikan entry baru jika nilai akun turun terlalu banyak dalam satu
hari.
Jika dinaikkan: bot diberi ruang rugi lebih besar.
Jika diturunkan: perlindungan lebih cepat aktif, tetapi peluang pemulihan pada
hari yang sama dapat terlewat.
## 8.4 Max spread (points)
Nilai default: 50.
Fungsi: menentukan biaya spread terbesar dalam satuan point yang masih boleh
dipertimbangkan.
Jika dinaikkan: entry lebih mudah saat spread mahal, tetapi biaya dan risiko
slippage meningkat.
Jika diturunkan: biaya lebih terjaga, tetapi transaksi lebih jarang.
## 8.5 Max spread / ATR
Nilai default: 0.35, artinya spread maksimal 35% dari ATR.
Fungsi: membandingkan spread dengan besar gerakan harga. Spread 30 points dapat
terasa murah saat harga bergerak besar, tetapi sangat mahal saat harga sepi.
Jika dinaikkan: bot lebih toleran terhadap spread.
Jika diturunkan: bot lebih ketat dan dapat lebih sering menolak entry.
## 8.6 Maks posisi terbuka total
Nilai default: 3.
Fungsi: membatasi seluruh transaksi yang masih terbuka pada simbol tersebut.
Jika dinaikkan: lebih banyak peluang dapat diambil, tetapi total risiko naik.
Jika diturunkan: risiko menumpuk lebih kecil.
## 8.7 Maks posisi untuk satu arah
Nilai default: 2.
Fungsi: membatasi jumlah BUY saja atau SELL saja. Nilai ini tidak boleh lebih
besar daripada batas posisi total.
Contoh: batas total 3 dan satu arah 2 berarti maksimal dua BUY, sedangkan satu
slot lain masih dapat digunakan sesuai aturan.
## 8.8 Periode ATR
Nilai default: 14.
Fungsi: menentukan berapa candle yang dipakai untuk menghitung rata-rata besar
gerakan harga.
Jika diturunkan: ATR lebih cepat berubah dan lebih sensitif.
Jika dinaikkan: ATR lebih stabil, tetapi lebih lambat menyesuaikan kondisi baru.
## 8.9 Stop Loss × ATR
Nilai default: 1.2.
Fungsi: menentukan jarak Stop Loss. Jika ATR bernilai 1, jarak SL kira-kira 1,2.
Jika dinaikkan: SL lebih jauh dan tidak mudah tersentuh, tetapi lot biasanya
menjadi lebih kecil serta jarak rugi lebih besar.
Jika diturunkan: SL lebih dekat, tetapi lebih mudah terkena gerakan harga kecil.
## 8.10 Take Profit × ATR
Nilai default: 1.8.
Fungsi: menentukan jarak target keuntungan.
Jika dinaikkan: target keuntungan lebih besar tetapi lebih sulit tercapai.
Jika diturunkan: target lebih mudah tercapai tetapi keuntungan per transaksi
menjadi lebih kecil.
## 8.11 Jarak minimum entry (ATR)
Nilai default: 0.5.
Fungsi: mencegah beberapa posisi dibuka terlalu berdekatan.
Jika dinaikkan: posisi lebih tersebar dan transaksi lebih jarang.
Jika diturunkan: bot dapat menambah posisi lebih dekat, tetapi risiko menumpuk
pada area harga yang sama meningkat.
## 8.11a Jarak maksimum momentum (ATR)
Nilai default: 0.55.
Fungsi: menentukan seberapa jauh harga boleh berada dari EMA cepat saat entry
momentum. Nilai lebih besar membuat bot lebih mudah mengikuti awal pergerakan,
tetapi terlalu besar dapat membuat bot mengejar harga yang sudah terlambat.
## 8.11b Tambahan threshold mode probe
Nilai default mode aktif: 0.02.
Fungsi: menaikkan nilai minimum entry ketika performa terbaru melemah. Nilai
lebih kecil menghasilkan lebih banyak entry dengan risiko yang tetap dikurangi.
## 8.11c Tambahan threshold spread tinggi
Nilai default mode aktif: 0.01.
Fungsi: menambah syarat ketika spread berada di atas 20% ATR. Nilai nol berarti
tidak ada tambahan skor, tetapi pengurangan risiko spread tetap berlaku.
## 8.11d Tambahan threshold spread sangat tinggi
Nilai default mode aktif: 0.03.
Fungsi: menambah syarat ketika spread berada di atas 25% ATR. Entry tetap
ditolak sepenuhnya jika melewati batas maksimum spread.
## 8.12 EMA tren cepat
Nilai default: 20.
Fungsi: garis rata-rata cepat untuk membaca arah utama M1.
Angka kecil lebih responsif tetapi lebih mudah berubah akibat gerakan acak.
Nilainya harus lebih kecil daripada EMA tren lambat.
## 8.13 EMA tren lambat
Nilai default: 50.
Fungsi: garis pembanding yang lebih stabil untuk menentukan arah tren.
Angka besar menghasilkan sinyal lebih tenang tetapi lebih lambat.
## 8.14 EMA entry cepat
Nilai default: 5.
Fungsi: membaca gerakan jangka sangat pendek untuk menentukan waktu masuk.
Nilainya harus lebih kecil daripada EMA entry lambat.
## 8.15 EMA entry lambat
Nilai default: 13.
Fungsi: pembanding EMA entry cepat untuk crossover, pullback, dan momentum.
## 8.16 Periode RSI
Nilai default: 14.
Fungsi: menentukan jumlah candle dalam perhitungan kekuatan gerakan.
Angka kecil lebih cepat berubah. Angka besar lebih stabil tetapi lebih lambat.
## 8.17 RSI BUY minimum
Nilai default: 55.
Fungsi: BUY hanya boleh dipertimbangkan jika RSI tidak kurang dari nilai ini.
Jika dinaikkan: konfirmasi BUY lebih kuat tetapi peluang lebih sedikit.
Jika diturunkan: BUY lebih mudah muncul tetapi sinyal lemah lebih banyak lolos.
## 8.18 RSI BUY maksimum
Nilai default: 100.
Fungsi: batas RSI tertinggi untuk BUY. Nilai 100 berarti pada praktiknya tidak
memberi batas atas tambahan.
Menurunkannya dapat mencegah BUY saat harga dinilai sudah terlalu panas, tetapi
juga dapat melewatkan tren kuat.
## 8.19 RSI SELL minimum
Nilai default: 0.
Fungsi: batas RSI terendah untuk SELL. Nilai 0 berarti tidak memberi batas bawah
tambahan.
Menaikkannya dapat mencegah SELL ketika penurunan sudah terlalu jauh, tetapi juga
dapat melewatkan tren turun kuat.
## 8.20 RSI SELL maksimum
Nilai default: 45.
Fungsi: SELL hanya boleh dipertimbangkan jika RSI tidak lebih besar dari nilai
ini.
Jika diturunkan: SELL memerlukan tekanan turun lebih kuat.
Jika dinaikkan: SELL lebih mudah muncul tetapi sinyal lemah lebih banyak lolos.
## 8.21 Volatilitas ATR minimum
Nilai default: 0.5.
Fungsi: menolak pasar yang terlalu sepi dibanding keadaan biasanya.
Jika dinaikkan: bot menunggu pergerakan lebih aktif.
Jika diturunkan: bot lebih mudah trading saat pasar tenang.
## 8.22 Volatilitas ATR maksimum
Nilai default: 2.5.
Fungsi: menolak pasar yang bergerak terlalu ekstrem dibanding keadaan biasanya.
Jika dinaikkan: bot lebih toleran terhadap lonjakan.
Jika diturunkan: perlindungan terhadap gerakan ekstrem lebih ketat.
Nilai minimum harus lebih kecil daripada nilai maksimum.
## 8.23 Break-even aktif
Nilai default: true, artinya aktif. false berarti tidak aktif.
Fungsi: mengizinkan SL dipindahkan mendekati harga masuk setelah posisi untung.
Keuntungan: dapat mengurangi kemungkinan posisi untung berubah menjadi loss.
Kekurangan: posisi dapat tertutup terlalu cepat sebelum tren berlanjut.
## 8.24 Trigger break-even (ATR)
Nilai default: 1.0.
Fungsi: menentukan seberapa jauh harga harus bergerak menguntungkan sebelum
break-even aktif.
Nilai kecil membuat perlindungan lebih cepat, tetapi lebih mudah terkena
pembalikan kecil. Nilai besar memberi ruang lebih luas.
## 8.25 Offset break-even (points)
Nilai default: 2.0.
Fungsi: menempatkan SL beberapa points melewati harga masuk agar dapat menutup
sedikit keuntungan atau membantu menutup biaya.
Offset terlalu besar dapat membuat perubahan SL ditolak broker atau terlalu
dekat dengan harga berjalan.
## 8.26 Trailing stop aktif
Nilai default: true.
Fungsi: mengizinkan SL mengikuti harga saat keuntungan bertambah.
Keuntungan: membantu mengunci keuntungan.
Kekurangan: trailing terlalu dekat dapat menutup transaksi sebelum tren selesai.
## 8.27 Trigger trailing (ATR)
Nilai default: 1.5.
Fungsi: menentukan keuntungan minimum sebelum trailing mulai bekerja.
Nilai kecil membuat trailing lebih cepat aktif. Nilai besar menunggu keuntungan
lebih jauh.
## 8.28 Jarak trailing (ATR)
Nilai default: 0.8.
Fungsi: menentukan jarak antara harga berjalan dan trailing Stop Loss.
Nilai kecil lebih ketat dan cepat mengunci hasil. Nilai besar memberi ruang
harga bergerak tetapi mengembalikan lebih banyak keuntungan ketika berbalik.
## 8.29 Jam trading mulai
Nilai default: 0, yaitu pukul 00.00 waktu komputer.
Fungsi: menentukan jam paling awal bot boleh membuka transaksi.
## 8.30 Jam trading selesai
Nilai default: 24, yaitu hingga akhir hari.
Fungsi: menentukan batas akhir waktu entry. Jam mulai harus lebih kecil daripada
jam selesai. Posisi yang sudah terbuka tetap dapat dikelola di luar jam entry.
Waktu chart MT5 dapat berbeda dari waktu komputer karena broker memakai zona
waktu server sendiri.
## 8.31 Login MT5
Fungsi: nomor akun MetaTrader 5. Hanya boleh berisi angka.
Kosongkan jika bot cukup memakai akun yang sudah login pada terminal MT5.
## 8.32 Password MT5
Fungsi: kata sandi akun MT5. Nilai ditampilkan sebagai karakter tersembunyi.
Jangan memasukkan password ke GitHub, screenshot, atau dokumentasi publik.
## 8.33 Server MT5
Fungsi: nama server broker, misalnya nama server demo atau live. Penulisannya
harus sama dengan informasi broker.
## 8.34 Path terminal64.exe
Path berarti alamat lokasi file di komputer. Pengaturan ini menunjukkan lokasi
program MT5, contohnya:
C:\Program Files\MetaTrader 5\terminal64.exe
Isi jika bot tidak menemukan terminal MT5 secara otomatis.
## 8.35 Token Telegram
Token adalah kunci rahasia yang diberikan oleh BotFather untuk mengendalikan bot
Telegram. Jangan membagikannya atau mengunggahnya ke GitHub.
Jika token pernah terlihat oleh orang lain, lakukan regenerate melalui BotFather.
## 8.36 Chat ID Telegram
Chat ID adalah nomor identitas percakapan tujuan. Ambil angka dari bagian:
"chat": {"id": 1992169291}
Jangan memakai message_id karena itu hanya nomor sebuah pesan.
## 8.37 Blackout berita
Blackout berarti waktu ketika bot dilarang membuka entry karena ada berita atau
waktu yang ingin dihindari.
Format:
13:25-13:40,19:55-20:15
Contoh tersebut memblokir entry pukul 13.25–13.40 dan 19.55–20.15 menurut waktu
komputer. Pisahkan beberapa rentang menggunakan koma.
## 8.38 URL kalender berita
Fungsi: alamat API yang menyediakan kalender ekonomi otomatis. URL harus dimulai
dengan https:// atau http://. Jika alamat tersebut memuat API key, aplikasi
menyembunyikannya seperti password.
Jika layanan gratis tidak mengizinkan endpoint kalender, kosongkan pengaturan
ini dan gunakan Blackout berita manual. Kegagalan API tidak menghentikan bot dan
percobaan ulang dibatasi sesuai interval refresh agar pembacaan chart tidak
terganggu oleh request berulang.
# 9. Arti tiga preset
## Konservatif
Risiko dan jumlah posisi lebih kecil. Syarat entry lebih ketat. Cocok untuk
pengujian awal dan pengguna yang lebih mengutamakan perlindungan modal.
## Seimbang
Menggunakan nilai tengah dan menjadi pilihan awal yang disarankan. Tetap dapat
mengalami loss.
## Aktif
Syarat entry lebih longgar dan risiko sedikit lebih tinggi. Peluang transaksi
bertambah, tetapi false signal dan kerugian juga dapat bertambah.
Preset bukan tombol untuk menjamin profit. Preset hanya mengisi beberapa nilai
awal yang masih dapat diubah.
# 10. Pengaturan yang saling berhubungan
- EMA cepat harus lebih kecil daripada EMA lambat.
- Maksimum posisi satu arah tidak boleh melebihi maksimum posisi total.
- RSI minimum tidak boleh lebih besar daripada RSI maksimum.
- Volatilitas minimum harus lebih kecil daripada volatilitas maksimum.
- Jam mulai harus lebih kecil daripada jam selesai.
- SL lebih jauh membuat lot hasil perhitungan biasanya lebih kecil.
- Spread/ATR ketat dan RSI ketat membuat entry lebih jarang.
- Jumlah posisi lebih besar tidak selalu menghasilkan profit lebih besar karena
total risiko juga bertambah.
- Break-even atau trailing yang terlalu cepat dapat memotong transaksi bagus.
# 11. Filter spread bertingkat
Bot membandingkan spread dengan ATR:

Contoh log spread sangat tinggi 26.9% ATR berarti biaya masuk cukup besar
dibanding gerakan harga. Sinyal masih dapat diperiksa, tetapi risiko diperkecil
dan nilai minimum entry dinaikkan.
# 12. Pengamanan kerugian
Pengaman utama meliputi:
- batas risiko per transaksi;
- batas total risiko seluruh posisi;
- batas posisi total dan per arah;
- batas drawdown harian, mingguan, dan dari nilai tertinggi;
- larangan menambah posisi searah yang sedang rugi;
- cooldown setelah loss;
- penghentian sementara setelah error order berulang;
- pemeriksaan performa transaksi terbaru;
- pemeriksaan margin akun;
- pemeriksaan aturan lot, SL, dan TP broker.
Pengaman dapat menyebabkan peluang bagus terlewat. Namun tanpa pengaman, satu
kondisi pasar buruk dapat menghasilkan rangkaian kerugian yang jauh lebih besar.
# 13. Cooldown yang berlaku
Nilai bawaan:
- setelah profit: tidak ada cooldown;
- setelah satu loss: 60 detik;
- setelah loss kedua berturut-turut: 180 detik;
- loss streak berat: dapat dijeda 10 menit;
- error order berulang: dapat dijeda 15 menit.
Bot tetap mengawasi posisi yang sudah terbuka selama cooldown. Yang dihentikan
sementara adalah entry baru.
# 14. Data yang disimpan
## trade_log.csv
Mencatat keadaan pasar dan rincian pada saat entry.
## closed_trade_log.csv
Mencatat transaksi yang sudah ditutup. File ini adalah sumber utama pengalaman
untung dan rugi.
## shadow_signal_log.csv
Mencatat sinyal yang ditolak. Data ini membantu membandingkan apakah penolakan
menyelamatkan akun dari loss atau justru melewatkan peluang.
## system_log.csv
Mencatat kejadian sistem, alasan pengaman aktif, error, dan keputusan learning.
## runtime_state.json
Menyimpan kondisi penting seperti nilai awal akun pada hari tersebut dan posisi
yang sedang dipantau agar tidak hilang ketika bot direstart.
Jangan menghapus file aktif tanpa memahami akibatnya karena pengalaman dan
pengamanan bot dapat kehilangan konteks.
# 15. Cara memahami win rate
Win rate adalah persentase transaksi yang menghasilkan profit.
Contoh:
win_rate: 0.6666666667
berarti sekitar 66,67%, atau kira-kira 4 transaksi untung dari 6 transaksi.
Win rate tinggi belum tentu menghasilkan keuntungan jika satu loss jauh lebih
besar daripada beberapa profit. Karena itu bot juga melihat:
- net profit: total keuntungan dikurangi total kerugian;
- profit factor: perbandingan jumlah profit dengan jumlah loss;
- average win: rata-rata nilai transaksi untung;
- average loss: rata-rata nilai transaksi rugi;
- expectancy: rata-rata hasil yang diharapkan dari setiap transaksi;
- drawdown: penurunan nilai akun.
# 16. Telegram untuk orang awam
Langkah ringkas:
- buat bot melalui BotFather;
- salin token;
- buka percakapan dengan bot yang dibuat;
- kirim /start;
- buka alamat getUpdates;
- ambil angka pada "chat":{"id":...};
- masukkan token dan Chat ID ke konfigurasi desktop;
- simpan dan restart bot;
- jalankan tes notifikasi.
Jika muncul chat not found, biasanya Chat ID salah atau pengguna belum mengirim
pesan /start.
# 17. Berita ekonomi
Berita ekonomi besar dapat membuat harga bergerak sangat cepat. Bot menyediakan:
- blackout manual yang selalu dapat digunakan;
- kalender otomatis jika pengguna memiliki API yang mendukung data kalender.
Jika API tidak termasuk dalam paket langganan atau endpoint dibatasi, kalender
otomatis tidak dapat dipakai. Blackout manual tetap tersedia.
API key juga merupakan rahasia dan tidak boleh dimasukkan ke GitHub.
# 18. Cara menjalankan desktop
- pasang MetaTrader 5;
- login ke akun demo;
- aktifkan Algo Trading;
- pasang AITradingDesktop-Setup-1.2.4.exe;
- buka tab Konfigurasi;
- pilih preset Seimbang sebagai awal;
- isi simbol broker dan data MT5 jika diperlukan;
- klik Simpan Konfigurasi;
- lakukan Tes Koneksi;
- klik Start Bot;
- pantau Live Engine Log.
Komputer pengguna tidak perlu memiliki Python jika menggunakan installer.
# 19. Cara membaca pesan penting

# 20. Mengapa peluang di chart tidak selalu diambil?
Beberapa alasan umum:
- arah harga belum cukup jelas;
- harga sudah terlalu jauh dan bot tidak ingin mengejar;
- RSI belum sesuai;
- garis EMA terlalu berdekatan sehingga pasar dianggap sideways;
- spread terlalu mahal;
- candle masih berjalan dan dapat berubah;
- learning score terlalu rendah;
- performa terbaru sedang melemah;
- cooldown atau kill-switch aktif;
- batas jumlah posisi sudah penuh;
- lot minimum broker terlalu berisiko;
- margin akun tidak cukup aman.
Peluang sering terlihat sangat jelas setelah harga selesai bergerak. Pada saat
entry harus dibuat, candle berikutnya belum diketahui. Keadaan ini disebut
hindsight atau melihat kejadian dengan pengetahuan setelah hasilnya terlihat.
# 21. Batas kemampuan bot
- Bot tidak mengetahui masa depan.
- Bot tidak dapat menjamin profit.
- M1 memiliki banyak gerakan acak.
- Spread dan slippage dapat berubah sangat cepat.
- Hasil akun demo dapat berbeda dari akun live.
- Data sedikit dapat menghasilkan kesimpulan yang salah.
- Model bagus pada data lama belum tentu bagus pada pasar baru.
- Berita mendadak dapat terjadi di luar kalender.
- Koneksi internet, MT5, broker, atau komputer dapat mengalami gangguan.
Slippage adalah perbedaan antara harga yang diminta dan harga yang benar-benar
diberikan broker.
# 22. Langkah aman sebelum memakai uang nyata
- gunakan akun demo;
- kumpulkan setidaknya 50–100 transaksi valid;
- jalankan bot pada beberapa keadaan pasar;
- periksa total profit, profit factor, dan drawdown;
- periksa apakah kerugian aktual sesuai batas yang direncanakan;
- bandingkan sinyal diterima dan sinyal bayangan;
- lakukan pengujian selama beberapa minggu;
- jangan memilih setting hanya karena hasil satu hari bagus;
- jika beralih ke akun live, mulai dari risiko terkecil;
- pantau bot dan jangan menganggapnya bebas perawatan.
# 23. File dan fungsi utama proyek
Bagian ini berguna bagi pengguna yang ingin mengetahui isi proyek. Pengguna
desktop biasa tidak harus membuka file-file ini.

# 24. Pengujian dan laporan
Menu atau perintah pemeriksaan kualitas data memastikan riwayat tidak rusak,
tidak berulang, dan mempunyai variasi hasil.
INVALID tidak selalu berarti seluruh proyek rusak. Contoh:
INVALID: baru 32 trade valid
berarti jumlah pengalaman belum mencapai minimal 50 untuk training model.
Laporan performa sebaiknya dibaca secara menyeluruh. Jangan hanya melihat win
rate. Perhatikan juga total keuntungan, besarnya rata-rata loss, profit factor,
dan drawdown.
# 25. Kesimpulan
AI Trading Bot sudah dapat:
- membaca harga MetaTrader 5;
- mencari BUY dan SELL secara seimbang;
- entry melalui crossover, continuation, dan momentum;
- menghitung risiko dan lot;
- memasang SL dan TP;
- mengelola break-even dan trailing stop;
- mencatat profit dan loss;
- menyesuaikan risiko dari pengalaman;
- melatih model AI setelah data cukup;
- menghentikan entry ketika keadaan dianggap tidak aman;
- mengirim notifikasi Telegram;
- dijalankan sebagai aplikasi Windows tanpa Python.
Tujuan bot adalah membuat keputusan lebih konsisten dan menjaga risiko. Bot tidak
dapat dibuat “sempurna” atau selalu profit. Hasil yang sehat harus dibuktikan
melalui data yang cukup, pengujian akun demo, dan pemantauan berkelanjutan.
| Keadaan spread | Tindakan bot |
| --- | --- |
| Sampai 20% dari ATR | Diproses normal |
| Lebih dari 20% sampai 25% | Risiko dikurangi dan syarat diperketat |
| Lebih dari 25% sampai 35% | Mode sangat hati-hati |
| Lebih dari 35% atau melewati batas points | Entry ditolak |
| Pesan | Arti sederhana |
| --- | --- |
| Sinyal: none | Syarat chart belum cukup |
| Sinyal: buy | Setup BUY ditemukan, tetapi masih ada pemeriksaan berikutnya |
| Sinyal: sell | Setup SELL ditemukan, tetapi masih ada pemeriksaan berikutnya |
| AI model belum tersedia | Model belum siap; aturan dan pembelajaran statistik tetap bekerja |
| score di bawah threshold | Nilai peluang belum mencapai syarat minimum |
| filter spread | Biaya masuk terlalu besar |
| filter volatilitas | Pasar terlalu sepi atau terlalu cepat |
| cooldown | Bot sedang menunggu setelah kejadian tertentu |
| kill-switch | Entry dihentikan sementara untuk melindungi akun |
| slot posisi penuh | Jumlah posisi sudah mencapai batas |
| order plan ditolak | Lot minimum atau risiko tidak aman |
| Order berhasil | Broker menerima order |
| profit=+... | Transaksi ditutup untung |
| profit=-... | Transaksi ditutup rugi |
| File | Fungsi dalam bahasa sederhana |
| --- | --- |
| main.py | Menjalankan seluruh urutan kerja bot |
| config.py | Menyimpan pengaturan |
| strategy.py | Menentukan arah dan sinyal |
| indicators.py | Menghitung EMA, RSI, dan ATR |
| risk_manager.py | Menghitung lot dan batas risiko |
| mt5_connector.py | Menghubungkan bot dengan MetaTrader 5 |
| learner.py | Menilai pengalaman transaksi |
| ai_trader.py | Melatih dan memakai model AI |
| market_filters.py | Memeriksa spread, volatilitas, dan cooldown |
| performance_guard.py | Menghentikan entry jika performa berbahaya |
| position_manager.py | Mengelola break-even dan trailing stop |
| trade_logger.py | Menyimpan catatan transaksi |
| notifier.py | Mengirim pesan Telegram |
| desktop_app.py | Menampilkan aplikasi desktop |