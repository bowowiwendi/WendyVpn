"""
Broadcast Template Module for WendyVpn Bot
===========================================
Port dari BotVPN2 (Aji) — broadcast dengan template siap pakai.

Fitur:
- Template Pengumuman 📢
- Template Informasi ℹ️
- Template Promo 🎉
- Custom message

Cara pakai: pilih template, edit teks, kirim ke semua user terdaftar.
"""
from kyt import *

BROADCAST_TEMPLATES = {
    "pengumuman": """📢 **PENGUMUMAN**

Halo pelanggan setia! 👋

[TULIS PENGUMUMAN DI SINI]

Terima kasih atas kepercayaannya! 🙏

🤖 @WendiVpn""",

    "informasi": """ℹ️ **INFORMASI**

[TULIS INFORMASI DI SINI]

Jika ada pertanyaan, hubungi admin.

🤖 @WendiVpn""",

    "promo": """🎉 **PROMO SPESIAL!**

🔥 [NAMA PROMO]

💰 Harga: [HARGA]
⏳ Berlaku sampai: [TANGGAL]

Jangan sampai kelewatan! 🚀

🤖 @WendiVpn""",
}


def _get_registered_users():
    """Ambil daftar user ID: /etc/bot/users.db dulu, fallback DB bot (user_services & user_balance)."""
    users = []
    try:
        with open("/etc/bot/users.db", "r") as f:
            for line in f:
                line = line.strip()
                if line and line.isdigit():
                    users.append(int(line))
    except Exception:
        pass
    if not users:
        try:
            import sqlite3
            for dbp in ("kyt/database.db", "/usr/bin/kyt/database.db", "database.db"):
                try:
                    db = sqlite3.connect(dbp)
                    for (tid,) in db.execute("SELECT DISTINCT telegram_id FROM user_services"):
                        users.append(int(tid))
                    for (tid,) in db.execute("SELECT DISTINCT telegram_id FROM user_balance"):
                        if int(tid) not in users:
                            users.append(int(tid))
                    db.close()
                    if users:
                        break
                except Exception:
                    continue
        except Exception:
            pass
    return users


@bot.on(events.CallbackQuery(data=b'broadcast-tpl'))
async def broadcast_tpl_menu(event):
    sender = await event.get_sender()
    if valid(str(sender.id)) != "true":
        await event.answer("Akses Ditolak", alert=True)
        return
    buttons = [
        [Button.inline("📢 Template Pengumuman", "bcast-tpl-pengumuman")],
        [Button.inline("ℹ️ Template Informasi", "bcast-tpl-informasi")],
        [Button.inline("🎉 Template Promo", "bcast-tpl-promo")],
        [Button.inline("✏️ Custom", "bcast-tpl-custom")],
        [Button.inline("‹ Kembali", "setting")],
    ]
    await event.edit("📢 **BROADCAST TEMPLATE**\n\nPilih template:", buttons=buttons)


@bot.on(events.CallbackQuery(pattern=r'^bcast-tpl-(\w+)$'))
async def broadcast_tpl_selected(event):
    sender = await event.get_sender()
    if valid(str(sender.id)) != "true":
        await event.answer("Akses Ditolak", alert=True)
        return
    tpl_name = event.pattern_match.group(1)
    chat = event.chat_id

    if tpl_name == "custom":
        template = "[TULIS PESAN DI SINI]"
    else:
        template = BROADCAST_TEMPLATES.get(tpl_name, "[TULIS PESAN DI SINI]")

    async with bot.conversation(chat) as conv:
        await event.respond(
            f"**Template {tpl_name}:**\n\n{template}\n\n"
            "**Ketik pesan final (atau /batal):**"
        )
        r = await conv.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
        pesan = r.raw_text.strip()
        if pesan == "/batal":
            await event.respond("❌ Dibatalkan.", buttons=[[Button.inline("‹ Kembali", "setting")]])
            return

    users = _get_registered_users()
    if not users:
        await event.respond("⚠️ Tidak ada user terdaftar.",
                            buttons=[[Button.inline("‹ Kembali", "setting")]])
        return

    msg = await event.respond(f"⏳ Mengirim ke {len(users)} user...")
    sukses = gagal = 0
    for uid in users:
        try:
            await bot.send_message(uid, pesan)
            sukses += 1
        except Exception:
            gagal += 1

    await msg.edit(
        f"✅ **Broadcast selesai**\n\n"
        f"✔️ Terkirim: `{sukses}`\n"
        f"❌ Gagal: `{gagal}`",
        buttons=[[Button.inline("‹ Kembali", "setting")]]
    )
