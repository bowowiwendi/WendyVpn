from kyt import *
import asyncio

def _api_check_state(name):
    try:
        return api_maintenance_command(name)
    except Exception:
        return "🔴 OFF"

@bot.on(events.CallbackQuery(data=b'reboot'))
async def rebooot(event):
    async def rebooot_(event):
        try:
            output = api_maintenance_command('reboot')
        except Exception as e:
            output = str(e)
        await event.respond(f"""{output}```
**» REBOOT SERVER**
» 🤖 @WendiVpn
""", buttons=[[Button.inline("‹ Kembali", "menu")]])
    sender = await event.get_sender()
    a = valid(str(sender.id))
    if a == "true":
        await rebooot_(event)
    else:
        await event.answer("Access Denied", alert=True)

@bot.on(events.CallbackQuery(data=b'resx'))
async def resx(event):
    async def resx_(event):
        msg = await event.respond("**🔄 Proses sedang berjalan...**")
        try:
            output = api_maintenance_command('systemctl restart xray')
            api_maintenance_command('systemctl restart nginx')
            api_maintenance_command('systemctl restart haproxy')
        except Exception as e:
            output = str(e)
        await event.respond(f"""
**» Restarting Service Done**
» 🤖 @WendiVpn
""", buttons=[[Button.inline("‹ Kembali", "menu")]])
        await msg.delete()
    sender = await event.get_sender()
    a = valid(str(sender.id))
    if a == "true":
        await resx_(event)
    else:
        await event.answer("Access Denied", alert=True)

@bot.on(events.CallbackQuery(data=b'speedtest'))
async def speedtest(event):
    async def speedtest_(event):
        msg = await event.respond("**🔄 Proses sedang berjalan...**")
        try:
            output = api_maintenance_command('speedtest-cli --share')
        except Exception as e:
            output = str(e)
        await event.respond(f"""
**
{output}
**
» 🤖 @WendiVpn
""", buttons=[[Button.inline("‹ Kembali", "menu")]])
        await msg.delete()
    sender = await event.get_sender()
    a = valid(str(sender.id))
    if a == "true":
        await speedtest_(event)
    else:
        await event.answer("Access Denied", alert=True)

@bot.on(events.CallbackQuery(data=b'backup'))
async def backup(event):
    async def backup_(event):
        msg = await event.respond("**🔄 Proses sedang berjalan...**")
        output = api_maintenance_command('bot-backup')
        await event.respond(f"""
**» BACKUP DONE**
» 🤖 @WendiVpn
""", buttons=[[Button.inline("‹ Kembali", "menu")]])
        await msg.delete()
    chat = event.chat_id
    sender = await event.get_sender()
    a = valid(str(sender.id))
    if a == "true":
        await backup_(event)
    else:
        await event.answer("Akses Ditolak", alert=True)

@bot.on(events.CallbackQuery(data=b'restore'))
async def restore(event):
    chat = event.chat_id
    sender = await event.get_sender()
    async def restore_(event):
        nonlocal chat, sender
        async with bot.conversation(chat) as user:
            await event.respond('**Input Link Backup:**')
            user = user.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
            user = (await user).raw_text.replace(" ", "")
            msg = await event.respond("**🔄 Proses sedang berjalan...**")
        try:
            a = api_maintenance_command("printf '%s\\n' '" + user + "' | bot-restore")
            await event.respond(f"**Successfully**", buttons=[[Button.inline("‹ Kembali", "menu")]])
            await msg.delete()
        except:
            await event.respond(f"**Link Not Found**", buttons=[[Button.inline("‹ Kembali", "menu")]])
            await msg.delete()
    a = valid(str(sender.id))
    if a == "true":
        await restore_(event)
    else:
        await event.answer("Akses Ditolak", alert=True)

@bot.on(events.CallbackQuery(data=b'fixdomain'))
async def fixcert(event):
    async def fixcert_(event):
        msg = await event.respond("**🔄 Proses sedang berjalan...**")
        api_maintenance_command('fixcert')
        await event.respond(f"""
**» FIX DOMAIN DONE**
» 🤖 @WendiVpn
""", buttons=[[Button.inline("‹ Kembali", "menu")]])
        await msg.delete()
    sender = await event.get_sender()
    a = valid(str(sender.id))
    if a == "true":
        await fixcert_(event)
    else:
        await event.answer("Access Denied", alert=True)

@bot.on(events.CallbackQuery(data=b'host'))
async def addhost(event):
    async def addhost_(event):
        async with bot.conversation(chat) as user:
            await event.respond('**Domain:**')
            user = user.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
            user = (await user).raw_text.replace(" ", "")
            msg = await event.respond("**🔄 Proses sedang berjalan...**")
        try:
            a = api_maintenance_command("printf '%s\\n' '" + user + "' | addhost")
        except:
            await event.respond(f"**Domain Gagal**", buttons=[[Button.inline("‹ Kembali", "menu")]])
        else:
            await event.respond(f"**Successfully**", buttons=[[Button.inline("‹ Kembali", "menu")]])
            await msg.delete()
    chat = event.chat_id
    sender = await event.get_sender()
    a = valid(str(sender.id))
    if a == "true":
        await addhost_(event)
    else:
        await event.answer("Access Denied", alert=True)

# ── TOGGLE HELPERS ────────────────────────────────────────────────────────
async def _check_auto_del():
    return _api_check_state('notif_delet')

async def _check_auto_backup():
    return _api_check_state('notif_backup')

async def _check_limit_ip():
    return _api_check_state('notif_limit')

async def _show_toggle_card(event, title, status, toggle_data, back_data="setting"):
    msg = f"""**⚙️ {title}**

**Status : {status}**

Gunakan tombol di bawah untuk mengaktifkan atau menonaktifkan."""
    await event.edit(msg, buttons=[
        [Button.inline(f"{'🔴 Nonaktifkan' if 'ON' in status else '🟢 Aktifkan'}", toggle_data)],
        [Button.inline("‹ Kembali", back_data)]
    ])

@bot.on(events.CallbackQuery(data=b'auto_delet'))
async def auto_delet(event):
    sender = await event.get_sender()
    if valid(str(sender.id)) != "true":
        await event.answer("Akses Ditolak", alert=True)
        return
    status = await _check_auto_del()
    await _show_toggle_card(event, "⏰ Auto Delete", status, "toggle-del")

@bot.on(events.CallbackQuery(data=b'toggle-del'))
async def toggle_del(event):
    sender = await event.get_sender()
    if valid(str(sender.id)) != "true":
        await event.answer("Akses Ditolak", alert=True)
        return
    status = await _check_auto_del()
    if "ON" in status:
        api_maintenance_command("printf '%s\\n' '3' | auto-delet.sh")
    else:
        api_maintenance_command("printf '%s\\n' '1' | auto-delet.sh")
    status = await _check_auto_del()
    await _show_toggle_card(event, "⏰ Auto Delete", status, "toggle-del")

@bot.on(events.CallbackQuery(data=b'auto_backup'))
async def auto_backup(event):
    sender = await event.get_sender()
    if valid(str(sender.id)) != "true":
        await event.answer("Akses Ditolak", alert=True)
        return
    status = await _check_auto_backup()
    await _show_toggle_card(event, "💾 Auto Backup", status, "toggle-backup")

@bot.on(events.CallbackQuery(data=b'toggle-backup'))
async def toggle_backup(event):
    sender = await event.get_sender()
    if valid(str(sender.id)) != "true":
        await event.answer("Akses Ditolak", alert=True)
        return
    status = await _check_auto_backup()
    if "ON" in status:
        api_maintenance_command("printf '%s\\n' '8' | auto-backup.sh")
    else:
        api_maintenance_command("printf '%s\\n' '3' | auto-backup.sh")
    status = await _check_auto_backup()
    await _show_toggle_card(event, "💾 Auto Backup", status, "toggle-backup")

@bot.on(events.CallbackQuery(data=b'limit'))
async def auto_limit(event):
    sender = await event.get_sender()
    if valid(str(sender.id)) != "true":
        await event.answer("Akses Ditolak", alert=True)
        return
    status = await _check_limit_ip()
    await _show_toggle_card(event, "🌐 Limit IP", status, "toggle-limit")

@bot.on(events.CallbackQuery(data=b'toggle-limit'))
async def toggle_limit(event):
    sender = await event.get_sender()
    if valid(str(sender.id)) != "true":
        await event.answer("Akses Ditolak", alert=True)
        return
    status = await _check_limit_ip()
    if "ON" in status:
        api_maintenance_command("printf '%s\\n' '1' | onoff")
    else:
        api_maintenance_command("printf '%s\\n' '2' | onoff")
    status = await _check_limit_ip()
    await _show_toggle_card(event, "🌐 Limit IP", status, "toggle-limit")

@bot.on(events.CallbackQuery(data=b'addbackup'))
async def add_backup(event):
    async def add_backup_(event):
        async with bot.conversation(chat) as user:
            await event.respond('**TOKEN API:**')
            user = user.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
            user = (await user).raw_text.replace(" ", "")
        async with bot.conversation(chat) as exp:
            await event.respond('**USER ID:**')
            exp = exp.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
            exp = (await exp).raw_text.replace(" ", "")
            msg = await event.respond("**🔄 Proses sedang berjalan...**")
            api_maintenance_command("printf '%s\\n' '" + user + "' '" + exp + "' | add-bot-notif")
            await event.respond(f"""
**» ADD BOT BACKUP N NOTIF SUKSES**
» 🤖 @WendiVpn
""",buttons=[[Button.inline("‹ Kembali","menu")]])
        await msg.delete()
    chat = event.chat_id
    sender = await event.get_sender()
    a = valid(str(sender.id))
    if a == "true":
        await add_backup_(event)
    else:
        await event.answer("Akses Ditolak",alert=True)

@bot.on(events.CallbackQuery(data=b'updatebot'))
async def update_bot(event):
    async def update_bot_(event):
        api_maintenance_command("printf '%s\\n' '23' | menu")
        await event.respond(f"""
**» UPDATE SCRIPT SUKSES**
» 🤖 @WendiVpn
""",buttons=[[Button.inline("‹ Kembali","menu")]])
    chat = event.chat_id
    sender = await event.get_sender()
    a = valid(str(sender.id))
    if a == "true":
        await update_bot_(event)
    else:
        await event.answer("Akses Ditolak",alert=True)

@bot.on(events.CallbackQuery(data=b'delbackup'))
async def del_backup(event):
    async def del_backup_(event):
        msg = await event.respond("**🔄 Proses sedang berjalan...**")
        api_maintenance_command('del-bot-notif')
        await event.respond(f"""
**» DELET BOT BACKUP N NOTIF DONE**
» 🤖 @WendiVpn
""",buttons=[[Button.inline("‹ Kembali","menu")]])
    sender = await event.get_sender()
    a = valid(str(sender.id))
    if a == "true":
        await del_backup_(event)
    else:
        await event.answer("Access Denied",alert=True)

@bot.on(events.CallbackQuery(data=b'killtrial'))
async def del_trial(event):
    async def del_trial_(event):
        msg = await event.respond("**🔄 Proses sedang berlangsung, harap tunggu...**")
        cmd = f'xp'
        try:
            output = api_maintenance_command(cmd)
            await event.respond(f"**Output:**\n```\n{output}\n```\n**» DELET ALL EXPIRED DONE**\n» 🤖 @WendiVpn", buttons=[[Button.inline("‹ Kembali", "menu")]])
        except subprocess.CalledProcessError as e:
            await event.respond(f"**❌ Error saat menjalankan skrip:** {str(e)}", buttons=[[Button.inline("‹ Kembali", "menu")]])
        await msg.delete()
    sender = await event.get_sender()
    a = valid(str(sender.id))
    if a == "true":
        await del_trial_(event)
    else:
        await event.answer("Access Denied",alert=True)

@bot.on(events.CallbackQuery(data=b'backer'))
async def backers(event):
    async def backers_(event):
        inline = [
[Button.inline("➕ Add Backup","addbackup"),
Button.inline("🗑️ Del Backup","delbackup")],
[Button.inline("📦 Backup","backup"),
Button.inline("📥 Restore","restore")],
[Button.inline("‹ Kembali","menu")]]
        z = requests.get(f"http://ip-api.com/json/?fields=country,region,city,timezone,isp").json()
        username = sender.username
        user_id = sender.id
        msg = f"""
💾 **BACKUP & RESTORE**

🌐 **Host** : `{DOMAIN}`
🆔 **ID** : `{user_id}` 👤 **@{username}**
"""
        await event.edit(msg,buttons=inline)
    sender = await event.get_sender()
    a = valid(str(sender.id))
    if a == "true":
        await backers_(event)
    else:
        await event.answer("Access Denied",alert=True)


@bot.on(events.CallbackQuery(data=b'setting'))
async def settings(event):
    async def settings_(event):
        inline = [
[Button.inline("🌐 Limit IP","limit")],
[Button.inline("🔧 Fix Domain","fixdomain"),
 Button.inline("🏠 Domain","host")],
[Button.inline("⏰ Auto Del","auto_delet"),
 Button.inline("💾 Auto Backup","auto_backup")],
[Button.inline("📦 DB Backup","backup_db_menu"),
 Button.inline("🚀 Speedtest","speedtest")],
[Button.inline("📦 Backup Restore","backer")],
[Button.inline("🔄 Reboot","reboot"),
Button.inline("🔄 Restart","resx")],
[Button.inline("🗑️ Del Expire","killtrial")],
[Button.inline("💰 Balance","adm-balance")],
[Button.inline("🔓 Del Lock","recovery")],
[Button.inline("🌐 API Remote","adm-api-servers")],
[Button.inline("📢 Broadcast","broadcast"),
Button.inline("⚙️ VAR","var-menu")],
[Button.inline("‹ Kembali","menu")]]
        z = requests.get(f"http://ip-api.com/json/?fields=country,region,city,timezone,isp").json()
        username = sender.username
        user_id = sender.id
        msg = f"""
⚙️ **SETTING MENU**

🌐 **Host** : `{DOMAIN}`
🆔 **ID** : `{user_id}` 👤 **@{username}**
"""
        await event.edit(msg,buttons=inline)
    sender = await event.get_sender()
    a = valid(str(sender.id))
    if a == "true":
        await settings_(event)
    else:
        await event.answer("Access Denied",alert=True)

# ── BROADCAST ────────────────────────────────────────────────────────────
@bot.on(events.CallbackQuery(data=b'broadcast'))
async def broadcast(event):
    chat = event.chat_id
    sender = await event.get_sender()
    if valid(str(sender.id)) != "true":
        await event.answer("Access Denied", alert=True)
        return
    async with bot.conversation(chat) as conv:
        await event.respond("📢 **Masukkan pesan broadcast:**\n\n_Pesan akan dikirim ke semua user terdaftar._")
        r = conv.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
        msg = (await r).raw_text
    await event.respond("⏳ **Mengirim broadcast...**")
    db = get_db()
    users = db.execute("SELECT telegram_id FROM user_balance").fetchall()
    sent = 0
    failed = 0
    for u in users:
        try:
            await bot.send_message(int(u['telegram_id']),
                f"📢 **BROADCAST**\n\n{msg}\n\n— *Admin*")
            sent += 1
            await asyncio.sleep(0.05)
        except:
            failed += 1
    await event.respond(f"✅ **Broadcast selesai!**\n\n📨 Terkirim: `{sent}`\n❌ Gagal: `{failed}`",
        buttons=[[Button.inline("‹ Kembali","setting")]])

# ── VAR CHANGE ───────────────────────────────────────────────────────────
def _var_path():
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'var.txt')

def _update_var(name, val):
    p = _var_path()
    with open(p, 'r') as f:
        lines = f.readlines()
    found = False
    for i, line in enumerate(lines):
        if line.startswith(name + '='):
            lines[i] = f"{name}='{val}'\n"
            found = True
            break
    if not found:
        lines.append(f"{name}='{val}'\n")
    with open(p, 'w') as f:
        f.writelines(lines)
    globals()[name] = val

@bot.on(events.CallbackQuery(data=b'var-menu'))
async def var_menu(event):
    sender = await event.get_sender()
    if valid(str(sender.id)) != "true":
        await event.answer("Access Denied", alert=True)
        return
    await event.edit("**⚙️ VARIABLE SETTINGS**\n\n"
        "Gunakan menu untuk mengubah variabel bot.\n\n"
        "⚠️ Setelah mengubah **BOT_TOKEN** atau **ADMIN**, restart bot diperlukan.",
        buttons=[
        [Button.inline("🤖 BOT_TOKEN","var-token")],
        [Button.inline("👤 ADMIN","var-admin")],
        [Button.inline("💳 P2P_API_KEY","var-bayar")],
        [Button.inline("🏪 STORE_NAME","var-store")],
        [Button.inline("📞 ADMIN_CONTACT","var-contact")],
        [Button.inline("‹ Kembali","setting")]])

@bot.on(events.CallbackQuery(func=lambda e: e.data.startswith(b'var-')))
async def var_change(event):
    data = event.data.decode()
    parts = data.split('-', 1)
    if len(parts) < 2 or parts[1] == 'menu':
        return
    var_type = parts[1]
    chat = event.chat_id
    sender = await event.get_sender()
    if valid(str(sender.id)) != "true":
        await event.answer("Access Denied", alert=True)
        return
    var_map = {
        'token': ('BOT_TOKEN', '🤖 **Masukkan BOT_TOKEN baru:**'),
        'admin': ('ADMIN', '👤 **Masukkan ADMIN ID baru:** (numeric)'),
        'bayar': ('P2P_API_KEY', '💳 **Masukkan P2P_API_KEY baru:**\nDibuat di dashboard https://p2p.shifastore.my.id (API Key)'),
        'store': ('STORE_NAME', '🏪 **Masukkan NAMA STORE baru:**'),
        'contact': ('ADMIN_CONTACT', '📞 **Masukkan link/username Telegram admin:**\nContoh: `https://t.me/WendiVpn`'),
    }
    if var_type not in var_map:
        return
    var_name, prompt = var_map[var_type]
    async with bot.conversation(chat) as conv:
        await event.respond(prompt)
        r = conv.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
        val = (await r).raw_text.strip()
    if not val:
        await event.respond("❌ **Nilai tidak boleh kosong.**",
            buttons=[[Button.inline("‹ Kembali","var-menu")]])
        return
    try:
        _update_var(var_name, val)
        await event.respond(f"✅ **{var_name} berhasil diubah!**\n\nNilai baru: `{val}`",
            buttons=[[Button.inline("‹ Kembali","var-menu")]])
    except Exception as e:
        await event.respond(f"❌ **Gagal:** `{e}`",
            buttons=[[Button.inline("‹ Kembali","var-menu")]])
