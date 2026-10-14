"""
CloudFront SSH Module for WendyVpn Bot
=======================================
Manajemen akun SSH via CloudFront (/cf-ssh path).
Direplikasi dari setup CloudFront di vps-utama & VPS Aji.

Fitur:
- Buat akun SSH CloudFront (trial & reguler)
- Perpanjang akun
- Hapus akun
- Cek login
- Info koneksi dengan format CloudFront

Kredensial CF dibaca dari /root/.cf-creds (dibuat oleh setup-cloudfront-ws.sh)
Domain CF dari /etc/xray/cf-domain atau fallback ke DOMAIN.
"""
from kyt import *
import random

# --- Helper: baca kredensial & domain CloudFront ---
def _cf_domain():
    """Ambil domain CloudFront dari /etc/xray/cf-domain, fallback ke DOMAIN."""
    try:
        with open("/etc/xray/cf-domain", "r") as f:
            d = f.read().strip()
            if d:
                return d
    except Exception:
        pass
    try:
        return DOMAIN
    except Exception:
        return ""

def _cf_creds():
    """Baca /root/.cf-creds -> dict. Return {} jika tidak ada."""
    creds = {}
    try:
        with open("/root/.cf-creds", "r") as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    creds[k.strip()] = v.strip().strip('"').strip("'")
    except Exception:
        pass
    return creds


# --- Menu utama CF SSH ---
@bot.on(events.CallbackQuery(data=b'cf-ssh'))
async def cf_ssh_menu(event):
    sender = await event.get_sender()
    if valid(str(sender.id)) != "true":
        await event.answer("Akses Ditolak", alert=True)
        return
    cf_domain = _cf_domain()
    creds = _cf_creds()
    status = "✅ Aktif" if creds else "⚠️ Kredensial CF belum ada\n(jalankan setup-cloudfront-ws.sh di VPS)"
    msg = f"""🌐 **SSH via CloudFront**

**Domain CF:** `{cf_domain}`
**Status:** {status}

Pilih aksi di bawah:"""
    buttons = [
        [Button.inline("➕ Buat Akun", "create-cf-ssh"),
         Button.inline("🎁 Trial", "trial-cf-ssh")],
        [Button.inline("🔄 Perpanjang", "renew-cf-ssh"),
         Button.inline("🗑️ Hapus", "delete-cf-ssh")],
        [Button.inline("👥 Cek Login", "login-cf-ssh")],
        [Button.inline("‹ Kembali", "ssh")],
    ]
    await event.edit(msg, buttons=buttons)


# --- Buat akun CF SSH ---
@bot.on(events.CallbackQuery(data=b'create-cf-ssh'))
async def create_cf_ssh(event):
    chat = event.chat_id
    sender = await event.get_sender()
    if valid(str(sender.id)) != "true":
        await event.answer("Akses Ditolak", alert=True)
        return
    cf_domain = _cf_domain()

    async with bot.conversation(chat) as conv:
        await event.respond("**👤 Username:**")
        r = await conv.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
        user = r.raw_text.strip()
        if not user or " " in user:
            await event.respond("❌ Username tidak valid.", buttons=[[Button.inline("‹ Kembali", "cf-ssh")]])
            return

        await event.respond("**🔑 Password:**")
        r = await conv.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
        pw = r.raw_text.strip()

        await event.respond("**⏳ Masa aktif (hari):**")
        r = await conv.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
        exp = r.raw_text.strip()
        if not exp.isdigit():
            await event.respond("❌ Harus angka.", buttons=[[Button.inline("‹ Kembali", "cf-ssh")]])
            return

        await event.respond("**📱 Limit IP (default 2):**")
        r = await conv.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
        limit_ip = r.raw_text.strip() or "2"

    try:
        api_create_account('ssh', user, password=pw, limit_ip=limit_ip, days=exp)
    except Exception as e:
        await event.respond(f"❌ Gagal: {e}", buttons=[[Button.inline("‹ Kembali", "cf-ssh")]])
        return

    today = DT.date.today()
    later = today + DT.timedelta(days=int(exp))
    msg = f"""🌐 **SSH via CloudFront**

👤 **Username:** `{user}`
🔑 **Password:** `{pw}`
🌐 **Domain CF:** `{cf_domain}`
📱 **Limit IP:** `{limit_ip}`
⏳ **Expired:** `{later}`

**◇━━━━━━━━━━◇**
**HTTP Custom / KPN Tunnel:**
- Host: `{cf_domain}`
- Port: `443`
- Path: `/cf-ssh`
- TLS: ON

**Payload contoh:**
```
GET /cf-ssh HTTP/1.1[crlf]Host: {cf_domain}[crlf]Upgrade: websocket[crlf][crlf]
```

💾 [Simpan Akun](https://{cf_domain}:443/cf-ssh-{user}.txt)
"""
    await event.respond(msg, buttons=[[Button.inline("‹ Kembali", "cf-ssh")]])


# --- Trial CF SSH ---
@bot.on(events.CallbackQuery(data=b'trial-cf-ssh'))
async def trial_cf_ssh(event):
    sender = await event.get_sender()
    if valid(str(sender.id)) != "true":
        await event.answer("Akses Ditolak", alert=True)
        return
    cf_domain = _cf_domain()

    async with bot.conversation(event.chat_id) as conv:
        await event.respond("**⏳ Pilih durasi trial:**", buttons=[
            [Button.inline("10 Menit", "cf-trial-10"), Button.inline("15 Menit", "cf-trial-15")],
            [Button.inline("30 Menit", "cf-trial-30"), Button.inline("60 Menit", "cf-trial-60")],
        ])
        r = await conv.wait_event(events.CallbackQuery)
        exp = r.data.decode("ascii").replace("cf-trial-", "")

    user = "cfTrial" + str(random.randint(100, 999))
    pw = "1"
    try:
        api_create_account('ssh', user, password=pw, limit_ip="2", days="1", trial=True)
    except Exception:
        await event.respond("❌ User sudah ada, coba lagi.", buttons=[[Button.inline("‹ Kembali", "cf-ssh")]])
        return

    msg = f"""🌐 **TRIAL SSH CloudFront**

👤 **Username:** `{user}`
🔑 **Password:** `{pw}`
🌐 **Domain CF:** `{cf_domain}`
⏳ **Durasi:** `{exp} Menit`

**HTTP Custom:**
- Host: `{cf_domain}`:443
- Path: `/cf-ssh`, TLS ON
"""
    await event.respond(msg, buttons=[[Button.inline("‹ Kembali", "cf-ssh")]])


# --- Perpanjang CF SSH ---
@bot.on(events.CallbackQuery(data=b'renew-cf-ssh'))
async def renew_cf_ssh(event):
    chat = event.chat_id
    sender = await event.get_sender()
    if valid(str(sender.id)) != "true":
        await event.answer("Akses Ditolak", alert=True)
        return
    async with bot.conversation(chat) as conv:
        await event.respond("**👤 Username yang diperpanjang:**")
        r = await conv.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
        user = r.raw_text.strip()
        await event.respond("**⏳ Tambah hari:**")
        r = await conv.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
        days = r.raw_text.strip()
    try:
        api_renew_account('ssh', user, days=days)
        await event.respond(f"✅ Akun `{user}` diperpanjang {days} hari.",
                            buttons=[[Button.inline("‹ Kembali", "cf-ssh")]])
    except Exception as e:
        await event.respond(f"❌ Gagal: {e}", buttons=[[Button.inline("‹ Kembali", "cf-ssh")]])


# --- Hapus CF SSH ---
@bot.on(events.CallbackQuery(data=b'delete-cf-ssh'))
async def delete_cf_ssh(event):
    chat = event.chat_id
    sender = await event.get_sender()
    if valid(str(sender.id)) != "true":
        await event.answer("Akses Ditolak", alert=True)
        return
    async with bot.conversation(chat) as conv:
        await event.respond("**👤 Username yang dihapus:**")
        r = await conv.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
        user = r.raw_text.strip()
    try:
        api_delete_account('ssh', user)
        await event.respond(f"✅ Akun `{user}` dihapus.",
                            buttons=[[Button.inline("‹ Kembali", "cf-ssh")]])
    except Exception as e:
        await event.respond(f"❌ Gagal: {e}", buttons=[[Button.inline("‹ Kembali", "cf-ssh")]])


# --- Cek login CF SSH ---
@bot.on(events.CallbackQuery(data=b'login-cf-ssh'))
async def login_cf_ssh(event):
    sender = await event.get_sender()
    if valid(str(sender.id)) != "true":
        await event.answer("Akses Ditolak", alert=True)
        return
    try:
        out = api_maintenance_command('cek-ssh-login')
    except Exception as e:
        out = str(e)
    await event.respond(f"```{out}```\n**» SSH Login via CF**",
                        buttons=[[Button.inline("‹ Kembali", "cf-ssh")]])
