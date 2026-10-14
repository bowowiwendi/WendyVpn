# 🤖 Wendi VPN Bot (@IdWendi_bot)

Bot Telegram VPN + PPOB berbasis Node.js + Telegraf.
Arsitektur terinspirasi BotVPN2, disesuaikan untuk Wendi.

## Fitur

| Kategori | Fitur |
|---|---|
| 🌐 VPN | SSH, VMess, VLess, Trojan — trial / create / renew / hapus |
| ☁️ CloudFront | Mode CF untuk semua protokol (`/cf-vmess`, `/cf-vless`, `/cf-trojan`, `/cf-ssh`) |
| 💳 PPOB | Deposit QRIS, cek saldo, beli pulsa/paket (Digiflazz), cek order |
| 📡 Kuota | Cek kuota HP via Sidompul |
| 👤 User | Akun Saya, statistik pribadi |
| 🛠️ Admin | Broadcast, tambah saldo, statistik global, cleanup |
| 🧹 Auto-cleanup | Hapus trial menumpuk & akun kadaluarsa otomatis (tiap 24 jam). Notif expire maks 1x per akun — anti spam |

## Struktur

```
.
├── app.js              # Entry point — menu, command, session
├── package.json
├── .env.example        # Contoh konfigurasi (copy jadi .env)
├── src/
│   ├── config.js       # Baca .env
│   ├── db.js           # SQLite (users, vpn_accounts, transactions)
│   └── digiflazz.js    # API Digiflazz (price list, transaksi)
└── modules/
    ├── vpn.js          # Create/renew/delete SSH, VMess, VLess, Trojan (+CF)
    ├── ppob.js         # Saldo, deposit QRIS, beli produk, cek order
    ├── kuota.js        # Cek kuota Sidompul
    ├── admin.js        # Helper admin (statistik, broadcast)
    └── cleanup.js      # Auto-cleanup + anti-spam notif expire
```

## Instalasi

```bash
# 1. Masuk direktori
cd wendi-bot-js

# 2. Install dependencies (butuh Node.js >= 18)
npm install

# 3. Buat .env dari contoh
cp .env.example .env
nano .env   # isi BOT_TOKEN dkk

# 4. Jalankan
npm start
```

### Menjalankan permanen (PM2)

```bash
npm install -g pm2
pm2 start app.js --name wendi-bot
pm2 save
pm2 startup
```

## Yang perlu disiapkan Wendi

1. **BOT_TOKEN** — token baru dari @BotFather (atau pakai token @IdWendi_bot yang lama;
   catatan: bot lama Python harus dimatikan dulu agar tidak rebutan token / 409 Conflict)
2. **ADMIN_ID** — sudah diisi `5162695441`
3. **VPN_API_BASE** — base URL API server VPN (format endpoint mengikuti pola
   `/createshh`, `/createvmess`, `/createvless`, `/createtrojan`, `/renew`, `/delete`
   seperti yang dipakai BotVPN2 di port 5888). Sesuaikan bila API di server beda.
4. **CloudFront** — `CF_DOMAIN`, `CF_VMESS_UUID`, `CF_VLESS_UUID`, `CF_TROJAN_PASSWORD`
   (kredensial yang sudah dibuat saat setup VPS Aji; untuk server Wendi isi sesuai
   kredensial CF di server masing-masing)
5. **Digiflazz** — `DIGIFLAZZ_USERNAME` + `DIGIFLAZZ_API_KEY` (untuk PPOB;
   akun masih Development Mode — Wendi menunda switch ke production)
6. **P2P Gateway** — `P2P_API_KEY` (untuk deposit QRIS via p2p.shifastore.my.id)
7. **Sidompul** — `SIDOMPUL_API_KEY` (untuk cek kuota; Wendi bilang API `#kuota` selalu diizinkan)

## Perintah user

- `/start` — menu utama
- `/saldo` — cek saldo
- `/produk` — daftar produk PPOB
- `/beli KODE TUJUAN` — beli pulsa/paket (contoh: `/beli TLKM5 083153170199`)
- `/cekorder REFID` — cek status order

## Perintah admin

- `/broadcast TEKS` — kirim pengumuman ke semua user
- `/addsaldo USERID NOMINAL` — tambah saldo manual
- `/cleanup` — jalankan cleanup sekarang
- `/cleanup dry` — lihat yang akan dihapus tanpa eksekusi

## Catatan migrasi dari bot Python lama

- Bot lama (`kyt.service` di vps-utama) harus di-stop/disable sebelum bot JS ini
  dijalankan dengan token yang sama, agar tidak terjadi 409 Conflict.
- Database terpisah (`data/bot.db`) — riwayat akun di DB lama tidak terbawa otomatis.
