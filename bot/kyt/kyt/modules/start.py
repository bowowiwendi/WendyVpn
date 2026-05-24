from kyt import *

@bot.on(events.CallbackQuery(data=b'start'))
async def start(event):
	inline = [
[Button.inline("⚡️CREATE ACCOUNT⚡️","menu")],
[Button.url("💌TELE GROUP💌","https://t.me/wendi_vpn"),
Button.url("☎️ORDER SC☎️","https://t.me/wendivpn")]]
	sender = await event.get_sender()
	val = valid(str(sender.id))
	if val == "true":
		sh = f' cat /etc/ssh/.ssh.db | grep "###" | wc -l'
		ssh = subprocess.check_output(sh, shell=True).decode("ascii")
		vm = f' cat /etc/vmess/.vmess.db | grep "###" | wc -l'
		vms = subprocess.check_output(vm, shell=True).decode("ascii")
		vl = f' cat /etc/vless/.vless.db | grep "###" | wc -l'
		vls = subprocess.check_output(vl, shell=True).decode("ascii")
		tr = f' cat /etc/trojan/.trojan.db | grep "###" | wc -l'
		trj = subprocess.check_output(tr, shell=True).decode("ascii")
		sdss = f" cat /etc/os-release | grep -w PRETTY_NAME | head -n1 | sed 's/=//g' | sed 's/PRETTY_NAME//g'"
		namaos = subprocess.check_output(sdss, shell=True).decode("ascii")
		ipvps = f" curl -s ipv4.icanhazip.com"
		ipsaya = subprocess.check_output(ipvps, shell=True).decode("ascii")
		citsy = f" cat /etc/xray/city"
		city = subprocess.check_output(citsy, shell=True).decode("ascii")
		username = sender.username
		user_id = sender.id
		msg = f"""
**◇━━━━━━━━━━◇** 
**⚡️ PREMIUM PANEL MENU ⚡️**
**◇━━━━━━━━━━◇** 
**»🔰 OS     :** `{namaos.strip().replace('"','')}`
**»🔰 CITY   :** `{city.strip()}`
**»🔰 DOMAIN :** `{DOMAIN}`
**»🔰 IP VPS :** `{ipsaya.strip()}`
**◇━━━━━━━━━━◇** 
**»🆔User ID :** `{user_id}`
**»👤Username:@{username}**
"""
		await event.edit(msg,buttons=inline)





