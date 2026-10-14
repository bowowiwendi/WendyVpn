# UPGRADE BOT TELEGRAM WENDYVPN
## Port Fitur BotVPN2 (Aji) + CloudFront SSH + Auto-Cleanup

Tanggal: 2026-10-14
Status: Siap integrasi (belum push)

---

## MODUL BARU (taruh di kyt/modules/)

| File | Fitur | Sumber |
|------|-------|--------|
| `cf_ssh.py` | SSH via CloudFront (/cf-ssh): buat, trial, renew, hapus, cek login | BARU |
| `cek_kuota.py` | Cek kuota HP via Sidompul API | Port BotVPN2 |
| `akun_saya.py` | Daftar akun dengan paginasi (/akunsaya) | Port BotVPN2 |
| `statistik.py` | Dashboard statistik VPN (/statistik) | Port BotVPN2 |
| `broadcast_tpl.py` | Broadcast dengan template (pengumuman/info/promo) | Port BotVPN2 |
| `auto_cleanup.py` | Auto-hapus trial kadaluarsa, expired, anti-spam notif | BARU |

Modul otomatis ter-load via ALL_MODULES (glob *.py di kyt/modules/).

---

## PATCH MENU

### PATCH-menu.py.txt
Tambahkan ke `kyt/modules/menu.py` fungsi `menu()`:
- Tombol "🌐 SSH CloudFront" → cf-ssh
- Tombol "👤 Akun Saya" → akun-saya
- Tombol "📊 Statistik" → statistik
- Tombol "📡 Cek Kuota" → cek-kuota
- Tombol "🧹 Cleanup" → cleanup

Command baru: /akunsaya, /statistik, /cekkuota, /cleanup, /cleanup_dry

### PATCH-ssh.py.txt
Tambahkan ke `kyt/modules/ssh.py` fungsi `ssh()`:
- Tombol "🌐 CloudFront Mode" → cf-ssh

---

## AUTO-CLEANUP

### Cara kerja
1. Baca DB akun dari /etc/ssh/.ssh.db, /etc/xray/config.json, dll (format ### user expiry)
2. Akun trial kadaluarsa → hapus langsung, tanpa notif
3. Akun reguler kadaluarsa → hapus otomatis, notif expire dikirim MAKSIMAL 1x
4. State di /etc/bot-cleanup/state.json mencegah hapus/notif ganda

### Cara pakai
- Manual: /cleanup (hapus) atau /cleanup_dry (simulasi)
- Otomatis: tambahkan cron `0 * * * *` yang memanggil fungsi run_cleanup()
  atau jalankan cleanup_scheduler() sebagai asyncio task di __main__.py

### Mencegah spam notif expire
Field `notified` di state.json menandai akun yang sudah dikirimi notif.
Akun yang sudah dihapus tidak akan dikirimi notif lagi.

---

## CLOUDFRONT SSH

### Prasyarat di VPS
1. Jalankan setup-cloudfront-ws.sh (sudah ada di repo WendyVpn/Features/)
2. File /root/.cf-creds terbuat otomatis
3. (Opsional) Set domain CF di /etc/xray/cf-domain

### Cara pakai di bot
Menu → SSH OVPN → CloudFront Mode (atau langsung dari menu utama)
- Buat akun: username, password, expiry, limit IP
- Output: format HTTP Custom dengan host CF, port 443, path /cf-ssh, TLS ON

---

## KENDALA / CATATAN

1. **BotVPN2 berbasis Node.js, bot Wendi Python** — port dilakukan per-fitur,
   bukan per-baris kode. Pola UI (tombol inline, paginasi) direplikasi.
2. **API Sidompul** memakai key dari BotVPN2 (mungkin perlu diganti jika expired).
3. **auto_cleanup** butuh akses baca ke /etc/*/  .db — pastikan bot jalan sebagai root.
4. **_get_registered_users()** di broadcast_tpl.py butuh file /etc/bot/users.db —
   sesuaikan dengan mekanisme user terdaftar yang sebenarnya.
5. Modul `p2p_pay.py` Wendi sudah ada (QRIS) — tidak diubah.
