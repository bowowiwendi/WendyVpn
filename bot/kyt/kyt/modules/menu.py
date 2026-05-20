from kyt import *

@bot.on(events.NewMessage(pattern=r"(?:.menu|/menu)$"))
@bot.on(events.CallbackQuery(data=b'menu'))
async def menu(event):
	inline = [
[Button.inline(" ⚡️SSH OVPN MANAGER⚡️ ","ssh")],
[Button.inline(" ⚡️VMESS⚡️ ","vmess"),
Button.inline(" ⚡️VLESS⚡️ ","vless")],
[Button.inline(" ⚡️TROJAN⚡️ ","trojan"),
Button.inline(" ⚡️SHDWSK⚡️ ","shadowsocks")],
[Button.inline(" ⚡️VPS INFO⚡️ ","info"),
Button.inline(" ⚡️SETTING⚡️ ","setting")],
[Button.inline(" ‹ ✨START✨› ","start")]]
	sender = await event.get_sender()
	val = valid(str(sender.id))
	if val == "false":
		try:
			await event.answer("Akses Ditolak", alert=True)
		except:
			await event.reply("Akses Ditolak")
	elif val == "true":
		sh = f' cat /etc/ssh/.ssh.db | grep "###" | wc -l'
		ssh = subprocess.check_output(sh, shell=True).decode("ascii")
		vm = f' cat /etc/xray/config.json | grep "###" | wc -l'
		vms = subprocess.check_output(vm, shell=True).decode("ascii")
		vl = f' cat /etc/vless/.vless.db | grep "###" | wc -l'
		vls = subprocess.check_output(vl, shell=True).decode("ascii")
		tr = f' cat /etc/trojan/.trojan.db | grep "###" | wc -l'
		trj = subprocess. check_output(tr, shell=True).decode("ascii")
		ss = f' cat /etc/shadowsocks/.shadowsocks.db | grep "###" | wc -l'
		ssk = subprocess. check_output(ss, shell=True).decode("ascii")
		sdss = f" cat /etc/os-release | grep -w PRETTY_NAME | head -n1 | sed 's/=//g' | sed 's/PRETTY_NAME//g'"
		namaos = subprocess.check_output(sdss, shell=True).decode("ascii")
		ipvps = f" curl -s ipv4.icanhazip.com"
		ipsaya = subprocess.check_output(ipvps, shell=True).decode("ascii")
		citsy = f" cat /etc/xray/city"
		city = subprocess.check_output(citsy, shell=True).decode("ascii")
		user_id = sender.id
		username = sender.username
		msg = f"""
**◇━━━━━━━━━━◇** 
**⚡️ PANEL MENU ADMIN ⚡️**
**◇━━━━━━━━━━◇** 
**»🔰OS     :** `{namaos.strip().replace('"','')}`
**»🔰CITY   :** `{city.strip()}`
**»🔰DOMAIN :** `{DOMAIN}`
**»🔰IP VPS :** `{ipsaya.strip()}`
**◇━━━━━━━━━━◇**
**»🔰Total Account Created:** 
**»🔰SSH OVPN    :** `{ssh.strip()}` __account__
**»🔰XRAY VMESS  :** `{vms.strip()}` __account__
**»🔰XRAY VLESS  :** `{vls.strip()}` __account__
**»🔰XRAY TROJAN :** `{trj.strip()}` __account__
**»🔰XRAY SHADOWSOCKS:** `{ssk.strip()}` __account__
**◇━━━━━━━━━━◇** 
**»🆔User ID:** `{user_id}`
**»👤Username:@{username}**
"""
		x = await event.edit(msg,buttons=inline)
		if not x:
			await event.reply(msg,buttons=inline)


