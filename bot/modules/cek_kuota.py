"""
Cek Kuota Module for WendyVpn Bot
==================================
Port dari BotVPN2 (Aji) — cek kuota via Sidompul API.

Fitur:
- /cekkuota atau tombol inline
- Input nomor HP, tampilkan sisa kuota
"""
from kyt import *
import re

SIDOMPUL_URL = "https://apigw.kmsp-store.com/sidompul/v4/cek_kuota"
SIDOMPUL_HEADERS = {
    'Authorization': 'Basic c2lkb21wdWxhcGk6YXBpZ3drbXNw',
    'X-API-Key': '60ef29aa-a648-4668-90ae-20951ef90c55',
    'X-App-Version': '4.0.0',
}


def _bersihkan_nomor(msisdn):
    msisdn = re.sub(r'[^0-9]', '', str(msisdn))
    if msisdn.startswith('62'):
        msisdn = '0' + msisdn[2:]
    return msisdn


def _format_kuota(data):
    """Format hasil cek kuota jadi pesan Telegram."""
    lines = ["📡 **CEK KUOTA**\n"]
    try:
        result = data.get('data', data)
        # Coba parse struktur umum
        if isinstance(result, dict):
            for k, v in result.items():
                if isinstance(v, (str, int, float)):
                    lines.append(f"• **{k}:** `{v}`")
                elif isinstance(v, list) and v:
                    lines.append(f"\n**{k}:**")
                    for item in v[:10]:
                        if isinstance(item, dict):
                            nama = item.get('nama_paket') or item.get('name') or item.get('package') or '-'
                            sisa = item.get('sisa') or item.get('remaining') or item.get('quota') or '-'
                            exp = item.get('expired') or item.get('expiry') or ''
                            lines.append(f"  ▫️ {nama}: `{sisa}` {exp}")
        else:
            lines.append(f"```{data}```")
    except Exception as e:
        lines.append(f"❌ Gagal parse: {e}")
    return "\n".join(lines)


@bot.on(events.CallbackQuery(data=b'cek-kuota'))
@bot.on(events.NewMessage(pattern=r'^/cekkuota$'))
async def cek_kuota_menu(event):
    sender = await event.get_sender()
    if valid(str(sender.id)) != "true":
        try:
            await event.answer("Akses Ditolak", alert=True)
        except Exception:
            await event.reply("Akses Ditolak")
        return
    chat = event.chat_id
    async with bot.conversation(chat) as conv:
        try:
            await event.respond("**📱 Masukkan nomor HP:**\nContoh: `083123456789`")
        except Exception:
            pass
        r = await conv.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
        nomor = _bersihkan_nomor(r.raw_text)

    if len(nomor) < 10:
        await event.respond("❌ Nomor tidak valid (minimal 10 digit).",
                            buttons=[[Button.inline("‹ Kembali", "menu")]])
        return

    msg = await event.respond("⏳ Mengecek kuota...")
    try:
        resp = requests.get(
            SIDOMPUL_URL,
            params={"msisdn": nomor, "isJSON": "true"},
            headers=SIDOMPUL_HEADERS,
            timeout=30,
        )
        if resp.status_code != 200:
            await msg.edit("❌ Server Sidompul gangguan.",
                           buttons=[[Button.inline("‹ Kembali", "menu")]])
            return
        data = resp.json()
        teks = _format_kuota(data)
        await msg.edit(f"{teks}\n\n📱 Nomor: `{nomor}`",
                       buttons=[[Button.inline("‹ Kembali", "menu")]])
    except Exception as e:
        await msg.edit(f"❌ Gagal: {e}",
                       buttons=[[Button.inline("‹ Kembali", "menu")]])
