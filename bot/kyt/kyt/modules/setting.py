from kyt import *
import asyncio

@bot.on(events.CallbackQuery(data=b'gen'))
async def create_ip(event):
	chat = event.chat_id
	sender = await event.get_sender()
	async def create_(event):
		async with bot.conversation(chat) as user:
			await event.respond('**ISI IP-YYYY-MM-DD:CONTOH 192.168.1.1-2030-01-30**')
			user = user.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			user = (await user).raw_text.replace(" ", "")
		msg = await event.respond("**🔄Proses sedang berjalan...**")
		cmd = f'printf "%s\n" "{user}" | bot-link.sh'
		try:
			subprocess.check_output(cmd, shell=True).decode("utf-8")
		except subprocess.CalledProcessError as e:
			await event.respond(f"**Error:** {e.output.decode('utf-8')}")
			return
		await event.respond(f"""
**SUCSESS GENERATE**
**» 🤖@WendiVpn** 
""",buttons=[[Button.inline("‹ Menu Utama ›","menu")]])
		await msg.delete()
	a = valid(str(sender.id))
	if a == "true":
		await create_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)

@bot.on(events.CallbackQuery(data=b'regis'))
async def create_ip(event):
	chat = event.chat_id
	sender = await event.get_sender()
	async def create_(event):
		async with bot.conversation(chat) as user:
			await event.respond('**DOMAIN:**')
			user = user.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			user = (await user).raw_text.replace(" ", "")
		async with bot.conversation(chat) as limit_ip:
			await event.respond("**SUBDOMAIN:**")
			limit_ip = limit_ip.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			limit_ip = (await limit_ip).raw_text.replace(" ", "")
		async with bot.conversation(chat) as pw:
			await event.respond("**IP VPS:**")
			pw = pw.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			pw = (await pw).raw_text.replace(" ", "")
			if not pw.isdigit():
				await event.respond("**IP harus berupa angka.**", buttons=[
					[Button.inline("🔄 Pointing Ulang","regis")],
					[Button.inline("❌ Cancel","setting")]])
				return  # Keluar dari fungsi jika pw bukan angka
			msg = await event.respond("**🔄Proses sedang berjalan...**")
			cmd = f'printf "%s\n" "{user}" "{limit_ip}" "{pw}" | cf.sh'
			try:
				subprocess.check_output(cmd, shell=True).decode("utf-8")
			except subprocess.CalledProcessError as e:
				await event.respond(f"**Error:** {e.output.decode('utf-8')}")
				return
			await event.respond(f"""
**SUCSESS POINTING IP**
**» 🤖@WendiVpn** 
""",buttons=[[Button.inline("‹ Menu Utama ›","menu")]])
			await msg.delete()
	a = valid(str(sender.id))
	if a == "true":
		await create_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)

@bot.on(events.CallbackQuery(data=b'reboot'))
async def rebooot(event):
    async def rebooot_(event):
        cmd = 'reboot'
        try:
            result = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
            output, _ = await result.communicate()
            output = output.decode('utf-8')
        except Exception as e:
            output = str(e)
        await event.respond(f"""{output}```
**» REBOOT SERVER**
**» 🤖@WendiVpn**
""", buttons=[[Button.inline("‹ Back ›", "menu")]])
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
        cmd = 'systemctl restart xray | systemctl restart nginx | systemctl restart haproxy | systemctl restart server | systemctl restart client'
        try:
            result = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
            output, _ = await result.communicate()
            output = output.decode('utf-8')
        except Exception as e:
            output = str(e)
        await event.respond(f"""
**» Restarting Service Done**
**» 🤖@WendiVpn**
""", buttons=[[Button.inline("‹ Back ›", "menu")]])
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
        cmd = 'speedtest-cli --share'
        try:
            result = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
            output, _ = await result.communicate()
            output = output.decode('utf-8')
        except Exception as e:
            output = str(e)
        await event.respond(f"""
**
{output}
**
**» 🤖@WendiVpn**
""", buttons=[[Button.inline("‹ Back ›", "menu")]])
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
        cmd = 'bot-backup'
        subprocess.check_output(cmd, shell=True)
        await event.respond(f"""
**» BACKUP DONE**
**» 🤖@WendiVpn**
""", buttons=[[Button.inline("‹ Back ›", "menu")]])
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
    async def restore_(event):
        async with bot.conversation(chat) as user:
            await event.respond('**Input Link Backup:**')
            user = user.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
            user = (await user).raw_text.replace(" ", "")
            msg = await event.respond("**🔄 Proses sedang berjalan...**")
            cmd = f'printf "%s\n" "{user}" | bot-restore'
        try:
            a = subprocess.check_output(cmd, shell=True).decode("utf-8")
        except:
            await event.respond(f"**Link Not Found**", buttons=[[Button.inline("‹ Back ›", "menu")]])
        else:
            await event.respond(f"**Successfully**", buttons=[[Button.inline("‹ Back ›", "menu")]])
            await msg.delete()
    chat = event.chat_id
    sender = await event.get_sender()
    a = valid(str(sender.id))
    if a == "true":
        await restore_(event)
    else:
        await event.answer("Akses Ditolak", alert=True)

@bot.on(events.CallbackQuery(data=b'fixdomain'))
async def fixcert(event):
    async def fixcert_(event):
        msg = await event.respond("**🔄 Proses sedang berjalan...**")
        cmd = 'fixcert'
        subprocess.check_output(cmd, shell=True)
        await event.respond(f"""
**» FIX DOMAIN DONE**
**» 🤖@WendiVpn**
""", buttons=[[Button.inline("‹ Back ›", "menu")]])
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
            cmd = f'printf "%s\n" "{user}" | addhost'
        try:
            a = subprocess.check_output(cmd, shell=True).decode("utf-8")
        except:
            await event.respond(f"**Domain Gagal**", buttons=[[Button.inline("‹ Back ›", "menu")]])
        else:
            await event.respond(f"**Successfully**", buttons=[[Button.inline("‹ Back ›", "menu")]])
            await msg.delete()
    chat = event.chat_id
    sender = await event.get_sender()
    a = valid(str(sender.id))
    if a == "true":
        await addhost_(event)
    else:
        await event.answer("Access Denied", alert=True)

@bot.on(events.CallbackQuery(data=b'auto_delet'))
async def auto_delet(event):
    async def auto_delet_(event):
        msg = await event.respond("**🔄 Proses sedang berjalan...**")
        cmd = 'notif_delet'.strip()
        x = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
        print(x)
        z = subprocess.check_output(cmd, shell=True).decode("utf-8")
        await event.respond(f"""
{z}""")
        async with bot.conversation(chat) as exp:
            await event.respond("**Pilih**",buttons=[
                [Button.inline(" ON ","1"),
                 Button.inline(" OFF ","2")],
                [Button.inline("‹ Main Setting ›", "setting")]])
            exp = exp.wait_event(events.CallbackQuery)
            exp = (await exp).data.decode("ascii")
        cmd = f'printf "%s\n" "{exp}" | auto-delet.sh'
        subprocess.check_output(cmd, shell=True)
        await event.respond(f"""
**» SUKSES SETTING AUTO DEL**
**» 🤖@WendiVpn**
""", buttons=[[Button.inline("‹ Back ›", "menu")]])
        await msg.delete()
    chat = event.chat_id
    sender = await event.get_sender()
    a = valid(str(sender.id))
    if a == "true":
        await auto_delet_(event)
    else:
        await event.answer("Akses Ditolak", alert=True)

@bot.on(events.CallbackQuery(data=b'auto_backup'))
async def auto_backup(event):
    async def auto_backup_(event):
        msg = await event.respond("**🔄 Proses sedang berjalan...**")
        cmd = 'notif_backup'.strip()
        x = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
        print(x)
        z = subprocess.check_output(cmd, shell=True).decode("utf-8")
        await event.respond(f"""
{z}""")
        async with bot.conversation(chat) as exp:
            await event.respond("**Pilih**",buttons=[
                [Button.inline(" ON ","6"),
                Button.inline(" OFF ","8")],
                [Button.inline("‹ Main Setting ›", "setting")]])
            exp = exp.wait_event(events.CallbackQuery)
            exp = (await exp).data.decode("ascii")
        cmd = f'printf "%s\n" "{exp}" | auto-backup.sh'
        subprocess.check_output(cmd, shell=True)
        await event.respond(f"""
**» SUKSES SETTING AUTO BACKUP**
**» 🤖@WendiVpn**
""", buttons=[[Button.inline("‹ Main Setting ›", "setting")]])
        await msg.delete()
    chat = event.chat_id
    sender = await event.get_sender()
    a = valid(str(sender.id))
    if a == "true":
        await auto_backup_(event)
    else:
        await event.answer("Akses Ditolak", alert=True)

@bot.on(events.CallbackQuery(data=b'limit'))
async def auto_limit(event):
    async def auto_limit_(event):
        msg = await event.respond("**🔄 Proses sedang berjalan...**")
        cmd = 'notif_limit'.strip()
        x = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
        print(x)
        z = subprocess.check_output(cmd, shell=True).decode("utf-8")
        await event.respond(f"""
{z}""")
        async with bot.conversation(chat) as exp:
            await event.respond("**Pilih**",buttons=[
                [Button.inline(" ON ","1"),
                Button.inline(" OFF ","2")]])
            exp = exp.wait_event(events.CallbackQuery)
            exp = (await exp).data.decode("ascii")
        cmd = f'printf "%s\n" "{exp}" | onoff'
        subprocess.check_output(cmd, shell=True)
        await event.respond(f"""
**» SUKSES SETTING LIMIT IP**
**» 🤖@WendiVpn**
""",buttons=[[Button.inline("‹ Main Setting ›", "setting")]])
        await msg.delete()
    chat = event.chat_id
    sender = await event.get_sender()
    a = valid(str(sender.id))
    if a == "true":
        await auto_limit_(event)
    else:
        await event.answer("Akses Ditolak", alert=True)

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
            cmd = f'printf "%s\n" "{user}" "{exp}" | add-bot-notif'
            subprocess.check_output(cmd, shell=True)
            await event.respond(f"""
**» ADD BOT BACKUP N NOTIF SUKSES**
**» 🤖@WendiVpn**
""",buttons=[[Button.inline("‹ Back ›","menu")]])
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
        cmd = f'printf "%s\n" "23" | menu'
        await event.respond(f"""
**» UPDATE SCRIPT SUKSES**
**» 🤖@WendiVpn**
""",buttons=[[Button.inline("‹ Back ›","menu")]])
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
        cmd = f'del-bot-notif'
        await event.respond(f"""
**» DELET BOT BACKUP N NOTIF DONE**
**» 🤖@WendiVpn**
""",buttons=[[Button.inline("‹ Back ›","menu")]])
    sender = await event.get_sender()
    a = valid(str(sender.id))
    if a == "true":
        await del_backup_(event)
    else:
        await event.answer("Access Denied",alert=True)

@bot.on(events.CallbackQuery(data=b'killtrial'))
async def del_trial(event):
    async def del_trial_(event):
        msg = await event.respond("**🔄 Proses sedang berlangsung, harap tunggu...**")  # Tambahkan pesan proses
        cmd = f'xp'
        try:
            output = subprocess.check_output(cmd, shell=True).decode("utf-8")  # Menjalankan skrip
            await event.respond(f"**Output:**\n```\n{output}\n```", buttons=[[Button.inline("‹ Back ›", "menu")]])
        except subprocess.CalledProcessError as e:
            await event.respond(f"**❌ Error saat menjalankan skrip:** {str(e)}", buttons=[[Button.inline("‹ Back ›", "menu")]])
        await event.respond(f"""
**» DELET ALL EXPIRED DONE**
**» 🤖@WendiVpn**
""",buttons=[[Button.inline("‹ Back ›","menu")]])
        await msg.delete()  # Menghapus pesan setelah proses selesai
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
[Button.inline(" 💾 Add Bot Backup","addbackup"),
Button.inline(" 🗑️ Del Bot Backup","delbackup")],
[Button.inline(" 📦 BACKUP","backup"),
Button.inline(" 📥 RESTORE","restore")],
[Button.inline("‹ Back ›","menu")]]
        z = requests.get(f"http://ip-api.com/json/?fields=country,region,city,timezone,isp").json()
        username = sender.username
        user_id = sender.id
        msg = f"""
**◇━━━━━━━━━━◇** 
            **⚡️ PREMIUM PANEL MENU ⚡️**
**◇━━━━━━━━━━◇** 
**»🔰Hostname/IP:** `{DOMAIN}`
**»🔰ISP:** `{z["isp"]}`
**»🔰Country:** `{z["country"]}`
**◇━━━━━━━━━━◇** 
**»🆔User ID:** `{user_id}`
**»👤Username:@{username}**
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
[Button.inline(" LIMIT IP ","limit"),
Button.inline(" POINT IP ","regis")],
[Button.inline(" FIX DOMAIN ","fixdomain"),
Button.inline(" DOMAIN ","host")],
[Button.inline(" AUTO DEL ","auto_delet"),
Button.inline(" AUTO BACK ","auto_backup")],
[Button.inline(" SPDTEST ","speedtest"),
Button.inline(" BACK & REST ","backer")],
[Button.inline(" REBOOT ","reboot"),
Button.inline(" RESTART ","resx")],
[Button.inline(" DEL EXPIRE ","killtrial"),
Button.inline(" REGIS VPS ","regist")],
[Button.inline(" DEL LOCK ","recovery"),
Button.inline(" GEN LINK ","gen")],
[Button.inline("‹ Back ›","menu")]]
        z = requests.get(f"http://ip-api.com/json/?fields=country,region,city,timezone,isp").json()
        username = sender.username
        user_id = sender.id
        msg = f"""
**◇━━━━━━━━━━◇** 
**⚡️ SETTING MENU ⚡️**
**◇━━━━━━━━━━◇** 
**»🔰Hostname/IP:** `{DOMAIN}`
**»🔰ISP:** `{z["isp"]}`
**»🔰Country:** `{z["country"]}`
**◇━━━━━━━━━━◇**
**»🆔User ID:** `{user_id}`
**»👤Username:@{username}** 
"""
        await event.edit(msg,buttons=inline)
    sender = await event.get_sender()
    a = valid(str(sender.id))
    if a == "true":
        await settings_(event)
    else:
        await event.answer("Access Denied",alert=True)
