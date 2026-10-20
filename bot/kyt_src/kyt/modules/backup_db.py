from kyt import *
import asyncio

def _init_config():
    db = get_db()
    db.execute("CREATE TABLE IF NOT EXISTS bot_config (key TEXT PRIMARY KEY, value TEXT)")
    db.execute("INSERT OR IGNORE INTO bot_config (key, value) VALUES ('auto_db_backup', 'disabled')")
    db.execute("INSERT OR IGNORE INTO bot_config (key, value) VALUES ('auto_db_backup_last', '')")
    db.commit()

_init_config()

async def send_db_to_admins(caption=None):
    db_path = "kyt/database.db"
    if not os.path.exists(db_path):
        return
    admins = get_db().execute("SELECT user_id FROM admin").fetchall()
    now_str = DT.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cap = caption or f"📦 **Auto Backup Database**\n\n🕐 `{now_str}`\n\n_Bot database otomatis dikirim 2x sehari._"
    for admin in admins:
        try:
            await bot.send_file(int(admin['user_id']), db_path, caption=cap)
        except:
            pass

async def db_backup_scheduler():
    while True:
        await asyncio.sleep(3600)
        try:
            db = get_db()
            config = db.execute("SELECT value FROM bot_config WHERE key='auto_db_backup'").fetchone()
            if not config or config['value'] != 'enabled':
                continue
            last_row = db.execute("SELECT value FROM bot_config WHERE key='auto_db_backup_last'").fetchone()
            last_time = last_row['value'] if last_row else ''
            now = DT.datetime.now()
            if last_time:
                try:
                    last_dt = DT.datetime.strptime(last_time, '%Y-%m-%d %H:%M:%S')
                    diff = (now - last_dt).total_seconds()
                    if diff < 43200:
                        continue
                except:
                    pass
            await send_db_to_admins()
            db.execute("UPDATE bot_config SET value=? WHERE key='auto_db_backup_last'",
                (now.strftime('%Y-%m-%d %H:%M:%S'),))
            db.commit()
        except:
            pass



@bot.on(events.CallbackQuery(data=b'backup_db_manual'))
async def backup_db_manual(event):
    sender = await event.get_sender()
    if valid(str(sender.id)) != "true":
        await event.answer("Akses Ditolak", alert=True)
        return
    await event.answer("Mengirim database...", alert=True)
    await send_db_to_admins(caption="\U0001f4e6 **Manual Backup Database**\n\n_Database dikirim secara manual oleh admin._")

@bot.on(events.CallbackQuery(data=b'restore_db'))
async def restore_db(event):
    sender = await event.get_sender()
    if valid(str(sender.id)) != "true":
        await event.answer("Akses Ditolak", alert=True)
        return
    chat = event.chat_id
    async with bot.conversation(chat) as conv:
        await event.respond("\U0001f4e4 **Kirim file database.db** untuk direstore.\n\n"
            "File akan menggantikan database bot saat ini.\n"
            "\u26a0\ufe0f Bot akan otomatis restart setelah restore.")
        resp = conv.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
        msg = await resp
    if not msg.file or not msg.file.name or not msg.file.name.endswith('.db'):
        await event.respond("\u274c **File tidak valid.** Kirim file dengan ekstensi .db",
            buttons=[[Button.inline("\u2039 Kembali", "backup_db_menu")]])
        return
    try:
        db_path = "kyt/database.db"
        bak_path = f"kyt/database_backup_{DT.datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        if os.path.exists(db_path):
            os.rename(db_path, bak_path)
        await msg.download_media(db_path)
        await event.respond("\u2705 **Database berhasil direstore!**\n\n"
            f"Backup lama disimpan sebagai: `{bak_path}`\n"
            "Bot akan restart...",
            buttons=[[Button.inline("\u2039 Kembali", "menu")]])
        os._exit(0)
    except Exception as e:
        await event.respond(f"\u274c **Gagal restore:** `{e}`",
            buttons=[[Button.inline("\u2039 Kembali", "backup_db_menu")]])

@bot.on(events.CallbackQuery(data=b'backup_db_menu'))
async def backup_db_menu(event):
    sender = await event.get_sender()
    if valid(str(sender.id)) != "true":
        await event.answer("Akses Ditolak", alert=True)
        return
    db = get_db()
    config = db.execute("SELECT value FROM bot_config WHERE key='auto_db_backup'").fetchone()
    status = config['value'] if config else 'disabled'
    on_lbl = "\U0001f7e2 ON"
    off_lbl = "\U0001f534 OFF"
    label = on_lbl if status == "enabled" else off_lbl
    btn = "\U0001f534 Nonaktifkan" if label == on_lbl else "\U0001f7e2 Aktifkan"
    msg = "\u2699\ufe0f **Database Backup**\n\n**Auto Backup : " + label + "**\n\nBot database (`database.db`) akan dikirim otomatis ke admin 2x sehari (setiap 12 jam).\n\n**Manual:** Kirim database sekarang atau restore dari file sebelumnya."
    await event.edit(msg, buttons=[
        [Button.inline(btn, "toggle_db_backup")],
        [Button.inline("\U0001f4e4 Backup Manual", "backup_db_manual"),
         Button.inline("\U0001f4e5 Restore", "restore_db")],
        [Button.inline("\u2039 Kembali", "setting")]
    ])

@bot.on(events.CallbackQuery(data=b'auto_db_backup'))
async def auto_db_backup(event):
    sender = await event.get_sender()
    if valid(str(sender.id)) != "true":
        await event.answer("Akses Ditolak", alert=True)
        return
    db = get_db()
    config = db.execute("SELECT value FROM bot_config WHERE key='auto_db_backup'").fetchone()
    status = config['value'] if config else 'disabled'
    on_lbl = "\U0001f7e2 ON"
    off_lbl = "\U0001f534 OFF"
    label = on_lbl if status == "enabled" else off_lbl
    btn = "\U0001f534 Nonaktifkan" if label == on_lbl else "\U0001f7e2 Aktifkan"
    msg = "\u2699\ufe0f **Auto DB Backup**\n\n**Status : " + label + "**\n\nBot database (`database.db`) akan dikirim otomatis ke admin 2x sehari (setiap 12 jam).\n\nGunakan tombol di bawah untuk mengaktifkan atau menonaktifkan."
    await event.edit(msg, buttons=[
        [Button.inline(btn, "toggle_db_backup")],
        [Button.inline("\u2039 Kembali", "setting")]
    ])

@bot.on(events.CallbackQuery(data=b'toggle_db_backup'))
async def toggle_db_backup(event):
    sender = await event.get_sender()
    if valid(str(sender.id)) != "true":
        await event.answer("Akses Ditolak", alert=True)
        return
    db = get_db()
    config = db.execute("SELECT value FROM bot_config WHERE key='auto_db_backup'").fetchone()
    status = config['value'] if config else 'disabled'
    new_status = 'disabled' if status == 'enabled' else 'enabled'
    db.execute("UPDATE bot_config SET value=? WHERE key='auto_db_backup'", (new_status,))
    if new_status == 'enabled':
        now = DT.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        db.execute("UPDATE bot_config SET value=? WHERE key='auto_db_backup_last'", (now,))
    db.commit()
    on_lbl = "\U0001f7e2 ON"
    off_lbl = "\U0001f534 OFF"
    label = on_lbl if new_status == "enabled" else off_lbl
    btn = "\U0001f534 Nonaktifkan" if label == on_lbl else "\U0001f7e2 Aktifkan"
    msg = "\u2699\ufe0f **Auto DB Backup**\n\n**Status : " + label + "**\n\nBot database (`database.db`) akan dikirim otomatis ke admin 2x sehari (setiap 12 jam).\n\nGunakan tombol di bawah untuk mengaktifkan atau menonaktifkan."
    await event.edit(msg, buttons=[
        [Button.inline(btn, "toggle_db_backup")],
        [Button.inline("\u2039 Kembali", "setting")]
    ])
