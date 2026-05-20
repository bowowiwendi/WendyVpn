from kyt import *
import asyncio  # Tambahkan ini
import subprocess

@bot.on(events.CallbackQuery(data=b'add-vps'))
async def create_ip(event):
	chat = event.chat_id  # Pindahkan ini ke atas
	sender = await event.get_sender()
	async def create_(event):
		async with bot.conversation(chat) as ip:
			await event.respond('**⛩️REGIST IP VPS⛩️:**')
			ip = ip.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			ip = (await ip).raw_text.replace(" ", "")
			cmd_check = f'curl -sS https://raw.githubusercontent.com/bowowiwendi/ipvps/main/ip | grep "{ip}"'
			if subprocess.call(cmd_check, shell=True) == 0:
				await event.respond("**IP VPS sudah terdaftar. Apakah Anda ingin mendaftar ulang?**", buttons=[
[Button.inline("🔄 Daftar Ulang","add-vps"),
Button.inline("❌ Batal","regist")]])
				return
		async with bot.conversation(chat) as user:
			await event.respond("**🔶USER NAME VPS🔶:**")
			user = user.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			user = (await user).raw_text.replace(" ", "")
			cmd_check = f'curl -sS https://raw.githubusercontent.com/bowowiwendi/ipvps/main/ip | grep "{user}"'
			if subprocess.call(cmd_check, shell=True) == 0:
				await event.respond("**User VPS sudah terdaftar. Apakah Anda ingin mendaftar ulang?**", buttons=[
[Button.inline("🔄 Daftar Ulang","add-vps"),
Button.inline("❌ Batal","regist")]])
				return
		async with bot.conversation(chat) as exp:
			await event.respond("**📅Expired VPS📅:**",buttons=[
[Button.inline("📅 30 DAY 📅","30"),
Button.inline("📅 60 DAY 📅","60")],
[Button.inline("📅 90 DAY 📅","90"),
Button.inline("📅LIFETIME📅 ","lifetime")]])
			exp = exp.wait_event(events.CallbackQuery)
			exp = (await exp).data.decode("ascii")
			cmd = f'printf "%s\n" "{ip}" "{user}" "{exp}" | add-vps.sh'
		try:
			output = subprocess.check_output(cmd, shell=True).decode("utf-8")  # Simpan output
		except subprocess.CalledProcessError as e:
			await event.respond(f"**❌Regist IP Gagal❌** {str(e)}",buttons=[Button.inline("‹ Back ›","menu")])  # Menggunakan str(e) untuk mendapatkan pesan kesalahan
			return  # Tambahkan return untuk menghentikan eksekusi jika ada error
		await event.respond(f"""
**◇━━━━━━━━━━━━━━━━━━━━━━━◇**
	**💎SUCSESS REGIST VPS💎**
**◇━━━━━━━━━━━━━━━━━━━━━━━◇**
**💎UPDATE & UPGRADE UBUNTU 20💎**
**◇━━━━━━━━━━━━━━━━━━━━━━━◇**
`apt update && apt upgrade -y && update-grub && sleep 2 && reboot`
**◇━━━━━━━━━━━━━━━━━━━━━━━◇**
**💎INSTALL AUTO SCRIPT NEXT💎**
**◇━━━━━━━━━━━━━━━━━━━━━━━◇**
```sysctl -w net.ipv6.conf.all.disable_ipv6=1 && sysctl -w net.ipv6.conf.default.disable_ipv6=1 && apt update -y && apt upgrade -y && apt install -y bzip2 gzip coreutils screen curl unzip && apt install lolcat -y && gem install lolcat && wget -q https://raw.githubusercontent.com/bowowiwendi/WendyVpn/ABSTRAK/setup-main.sh && chmod +x setup-main.sh && sed -i -e 's/\r$//' setup-main.sh && screen -S setupku ./setup-main.sh```
**◇━━━━━━━━━━━━━━━━━━━━━━━◇**
**» 🤖@WendiVpn** 
""",buttons=[Button.inline("‹ Back ›","menu")])
	a = valid(str(sender.id))
	if a == "true":
		await create_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)

@bot.on(events.CallbackQuery(data=b'del-ip'))
async def delete_ip(event):
	async def delete_ip_(event):
		cmd = "curl -sS https://raw.githubusercontent.com/bowowiwendi/ipvps/main/ip | grep '^###' | cut -d ' ' -f 2-3 | sort | uniq | nl".strip()
		try:
			z = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
			await event.respond(f"""
**◇━━━━━━━━━━━━━━━━━━◇**
	** ⟨🔸 LIST SEWA VPS/SC🔸⟩**
**◇━━━━━━━━━━━━━━━━━━◇**
```
{z}
```
""",buttons=[[Button.inline("‹ cancel ›","menu")]])
		except subprocess.CalledProcessError as e:
			await event.respond(f"**❌ Error: {str(e)} ❌**", buttons=[[Button.inline("‹ cancel ›", "menu")]])
		async with bot.conversation(chat) as user:
			await event.respond('**🔶Masukan User:**')
			user = user.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			user = (await user).raw_text.replace(" ", "")
			cmd_check = f'curl -sS https://raw.githubusercontent.com/bowowiwendi/ipvps/main/ip | grep "{user}"'
			if subprocess.call(cmd_check, shell=True) != 0:
				await event.respond("**IP VPS tidak terdaftar.**", buttons=[
[Button.inline("🔄 Hapus Ulang","del-ip"),
Button.inline("❌ Batal","regist")]])
				return
			cmd = f'printf "%s\n" "{user}" | del-ip.sh'
			a = subprocess.check_output(cmd, shell=True).decode("utf-8")
			await event.respond(f"**✅Successfully Deleted✅** `{user}`",buttons=[Button.inline("‹ Back ›","menu")])
	chat = event.chat_id
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await delete_ip_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)

@bot.on(events.CallbackQuery(data=b're-ip'))
async def delete_ip(event):
	async def delete_ip_(event):
		cmd = "curl -sS https://raw.githubusercontent.com/bowowiwendi/ipvps/main/ip | grep '^###' | cut -d ' ' -f 2-3 | sort | uniq | nl".strip()
		try:
			z = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
			await event.respond(f"""
**◇━━━━━━━━━━━━━━━━━━◇**
	** ⟨🔸 LIST SEWA VPS/SC🔸⟩**
**◇━━━━━━━━━━━━━━━━━━◇**
```
{z}
```
""",buttons=[[Button.inline("‹ cancel ›","menu")]])
		except subprocess.CalledProcessError as e:
			await event.respond(f"**❌ Error: {str(e)} ❌**", buttons=[[Button.inline("‹ cancel ›", "menu")]])
		async with bot.conversation(chat) as user:
			await event.respond('**🔶Masukan User:**')
			user = user.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			user = (await user).raw_text.replace(" ", "")
			cmd_check = f'curl -sS https://raw.githubusercontent.com/bowowiwendi/ipvps/main/ip | grep "{user}"'
			if subprocess.call(cmd_check, shell=True) != 0:
				await event.respond("**IP VPS tidak terdaftar.**", buttons=[
[Button.inline("🔄 Renew Ulang","re-ip"),
Button.inline("❌ Batal","regist")]])
				return
		async with bot.conversation(chat) as bug:
			await event.respond("**⏳Expired VPS:**",buttons=[
[Button.inline(" ⏳30⏳ ","30"),
Button.inline(" ⏳60⏳ ","60")],
[Button.inline(" ⏳90⏳ ","90"),
Button.inline(" ⏳LIFETIME⏳ ","lifetime")]])
			bug = bug.wait_event(events.CallbackQuery)
			bug = (await bug).data.decode("ascii")
			cmd = f'printf "%s\n" "{user}" "{bug}" |renew-ip.sh'
			a = subprocess.check_output(cmd, shell=true).decode("utf-8")
			await event.respond(f"**Successfully Renew** `{user}`",buttons=[Button.inline("‹ Back ›","menu")])
	chat = event.chat_id
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await delete_ip_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)

@bot.on(events.CallbackQuery(data=b'ls-ip'))
async def ls_ip(event):
	async def ls_ip_(event):
		cmd = "curl -sS https://raw.githubusercontent.com/bowowiwendi/ipvps/main/ip | grep '^###' | cut -d ' ' -f 2-4 | sort | uniq | nl".strip()
		try:
			z = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
			await event.respond(f"""
**◇━━━━━━━━━━━━━━━━━━◇**
	** ⟨🔸 LIST SEWA VPS/SC🔸⟩**
**◇━━━━━━━━━━━━━━━━━━◇**
```
{z}
```
""",buttons=[[Button.inline("‹ Back ›","menu")]])
		except subprocess.CalledProcessError as e:
			await event.respond(f"**❌ Error: {str(e)} ❌**", buttons=[[Button.inline("‹ Back ›","menu")]])
	chat = event.chat_id
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await ls_ip_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)

@bot.on(events.CallbackQuery(data=b'cek'))
async def resx(event):
    async def resx_(event):  # Tambahkan pesan proses
        cmd = 'xpsc.sh'
        try:
            output = subprocess.check_output(cmd, shell=True).decode("utf-8")  # Menjalankan skrip
            await event.respond(f"**Output:**\n```\n{output}\n```", buttons=[[Button.inline("‹ Back ›", "menu")]])
        except subprocess.CalledProcessError as e:
            await event.respond(f"**❌ Error saat menjalankan skrip:** {str(e)}", buttons=[[Button.inline("‹ Back ›", "menu")]])
    sender = await event.get_sender()
    a = valid(str(sender.id))
    if a == "true":
        await resx_(event)
    else:
        await event.answer("Access Denied", alert=True)

@bot.on(events.CallbackQuery(data=b'ch-ip'))
async def delete_ip(event):
	async def delete_ip_(event):
		cmd = "curl -sS https://raw.githubusercontent.com/bowowiwendi/ipvps/main/ip | grep '^###' | cut -d ' ' -f 2-4 | sort | uniq | nl".strip()
		try:
			z = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
			await event.respond(f"""
**◇━━━━━━━━━━━━━━━━━━◇**
	** ⟨🔸 LIST SEWA VPS/SC🔸⟩**
**◇━━━━━━━━━━━━━━━━━━◇**
```
{z}
```
""",buttons=[[Button.inline("‹ cancel ›","menu")]])
		except subprocess.CalledProcessError as e:
			await event.respond(f"**❌ Error: {str(e)} ❌**", buttons=[[Button.inline("‹ cancel ›", "menu")]])
		async with bot.conversation(chat) as user:
			await event.respond('**♻INPUT IP OLD/LAMA:♻**')
			user = user.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			user = (await user).raw_text.replace(" ", "")
			cmd_check = f'curl -sS https://raw.githubusercontent.com/bowowiwendi/ipvps/main/ip | grep "{user}"'
			if subprocess.call(cmd_check, shell=True) != 0:
				await event.respond("**IP VPS tidak terdaftar.**", buttons=[
[Button.inline("🔄 Ganti IP Ulang","ch-ip"),
Button.inline("❌ Batal","regist")]])
				return
		async with bot.conversation(chat) as bug:
			await event.respond('**🆕INPUT IP NEW/BARU:🆕**')
			bug = bug.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			bug = (await bug).raw_text.replace(" ", "")
			cmd_check = f'curl -sS https://raw.githubusercontent.com/bowowiwendi/ipvps/main/ip | grep "{bug}"'
			if subprocess.call(cmd_check, shell=True) == 0:
				await event.respond("**IP VPS sudah terdaftar.**", buttons=[
[Button.inline("🔄 Ganti IP Ulang","ch-ip"),
Button.inline("❌ Batal","regist")]])
				return
			cmd = f'printf "%s\n" "{user}" "{bug}" |change-ip.sh'
			a = subprocess.check_output(cmd, shell=True).decode("utf-8")
			await event.respond(f"**Successfully Renew** `{user}`",buttons=[Button.inline("‹ Back ›","menu")])
	chat = event.chat_id
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await delete_ip_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)

@bot.on(events.CallbackQuery(data=b'regist'))
async def settings(event):
    async def settings_(event):
        inline = [
[Button.inline(" 🆕REGIST IP🆕 ","add-vps"),
Button.inline(" 🆕CHANGE IP🆕 ","ch-ip")],
[Button.inline(" 🗑️DELET IP🗑️ ","del-ip"),
Button.inline(" ✅CEK EXPIRED✅ ","cek")],
[Button.inline(" 📋LIST VPS📋 ","ls-ip"),
Button.inline(" 🔄RENEW IP🔄 ","re-ip")],
[Button.inline("‹ Back ›","menu")]]
        z = requests.get(f"http://ip-api.com/json/?fields=country,region,city,timezone,isp").json()
        msg = f"""
**◇━━━━━━━━━━━━━━━━━━━━━━━◇** 
**⚡️ REGIST SCRIPT ⚡️**
**◇━━━━━━━━━━━━━━━━━━━━━━━◇** 
**»🔰Hostname/IP:** `{DOMAIN}`
**»🔰ISP:** `{z["isp"]}`
**»🔰Country:** `{z["country"]}`
**◇━━━━━━━━━━━━━━━━━━━━━━━◇** 
""" 
        await event.edit(msg,buttons=inline)
    sender = await event.get_sender()
    if str(sender.id) in ["5162695441", "id_lainnya"]:
        await settings_(event)
    else:
        await event.answer("Access Denied",alert=True)
