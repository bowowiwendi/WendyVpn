from kyt import *

#detail
@bot.on(events.CallbackQuery(data=b'd-trojan'))
async def l_trojan(event):
	async def l_trojan_(event):
		cmd = 'cat /etc/xray/config.json | grep "^#!" | cut -d " " -f 2-3 | sort | uniq | nl'.strip()
		x = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
		print(x)
		z = subprocess.check_output(cmd, shell=True).decode("utf-8")
		await event.respond(f"""
**◇━━━━━━━━━━◇**
	** ⟨🔸 Trojan Account🔸⟩**
**◇━━━━━━━━━━◇**
```
{z}
```
""")
		async with bot.conversation(chat) as user:
			await event.respond(" **🔡Username:**")
			user_event = user.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			user = (await user_event).raw_text.replace(" ", "")
			cmd_check = f'cat /etc/xray/config.json | grep "{user}"'
			if subprocess.call(cmd_check, shell=True) != 0:
				await event.respond("**Username tidak ditemukan. Silakan masukkan username yang benar.**", buttons=[
[Button.inline("🔄 Ulangi","d-trojan")],
[Button.inline("❌ Cancel","trojan")]])
				return
			cmd = f'cat /var/www/html/trojan-{user}.txt'.strip()
			x = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
			print(x)
			z = subprocess.check_output(cmd, shell=True).decode("utf-8")
			if z:
				await event.respond(f"""
**◇━━━━━━━━━━◇**
	** ⟨🔸 Trojan Account🔸⟩**
**◇━━━━━━━━━━◇**
```
{z}
```
""",buttons=[[Button.inline("‹ Back ›","trojan")]])
			else:
				await event.respond("**Filed**: User tidak ditemukan", buttons=[[Button.inline("‹ Back ›","trojan")]])
	chat = event.chat_id
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await l_trojan_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)

#LOCK trojan
@bot.on(events.CallbackQuery(data=b'lock-trojan'))
async def lock_trojan(event):
	async def lock_trojan_(event):
		cmd = 'cat /etc/xray/config.json | grep "^#!" | cut -d " " -f 2-3 | sort | uniq | nl'.strip()
		x = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
		print(x)
		z = subprocess.check_output(cmd, shell=True).decode("utf-8")
		await event.respond(f"""
**◇━━━━━━━━━━◇**
	** ⟨🔸 Trojan Account🔸⟩**
**◇━━━━━━━━━━◇**
```
{z}
```
""")
		async with bot.conversation(chat) as user:
			await event.respond(" **🔡Username:**")
			user = user.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			user = (await user).raw_text.replace(" ", "")
			cmd_check = f'cat /etc/xray/config.json | grep "{user}"'
			if subprocess.call(cmd_check, shell=True) != 0:
				await event.respond("**Username tidak ditemukan. Silakan masukkan username yang benar.**", buttons=[
[Button.inline("🔄 Lock Ulang","lock-trojan")],
[Button.inline("❌ Cancel","trojan")]])
				return
			cmd = f'printf "%s\n" "{user}" | lock-tr'
		try:
			a = subprocess.check_output(cmd, shell=True).decode("utf-8")
		except subprocess.CalledProcessError:  # Menangani kesalahan jika user tidak ada
			await event.respond(f" **Successfully**", buttons=[[Button.inline("‹ Back ›","trojan")]])
		else:
			await event.respond(f" **Successfully Lock**", buttons=[[Button.inline("‹ Back ›","trojan")]])
	chat = event.chat_id
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await lock_trojan_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)
#UNLOCK trojan
@bot.on(events.CallbackQuery(data=b'unlock-trojan'))
async def unlock_trojan(event):
	async def unlock_trojan_(event):
		cmd = 'cat /etc/xray/.lock.db | grep "^#!" | cut -d " " -f 2-3 | sort | uniq | nl'.strip()
		x = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
		print(x)
		z = subprocess.check_output(cmd, shell=True).decode("utf-8")
		await event.respond(f"""
**◇━━━━━━━━━━◇**
	** ⟨🔸 Trojan Account🔸⟩**
**◇━━━━━━━━━━◇**
```
{z}
```
""")
		async with bot.conversation(chat) as user:
			await event.respond(" **🔡Username:**")
			user = user.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			user = (await user).raw_text.replace(" ", "")
			cmd_check = f'cat /etc/xray/.lock.db | grep "{user}"'
			if subprocess.call(cmd_check, shell=True) != 0:
				await event.respond("**Username tidak ditemukan. Silakan masukkan username yang benar.**", buttons=[
[Button.inline("🔄 Unlock Ulang","unlock-trojan")],
[Button.inline("❌ Cancel","trojan")]])
				return  # Keluar dari fungsi jika username tidak ditemukan
			cmd = f'printf "%s\n" "{user}" | unlock-tr'
		try:
			a = subprocess.check_output(cmd, shell=True).decode("utf-8")
		except subprocess.CalledProcessError:  # Menangani kesalahan jika user tidak ada
			await event.respond(f" **Successfully**", buttons=[[Button.inline("‹ Back ›","trojan")]])
		else:
			await event.respond(f" **Successfully Unlock**", buttons=[[Button.inline("‹ Back ›","trojan")]])
	chat = event.chat_id
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await unlock_trojan_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)


@bot.on(events.CallbackQuery(data=b'create-trojan'))
async def create_trojan(event):
	async def create_trojan_(event):
		async with bot.conversation(chat) as user:
			await event.respond('🔡**Username:**')
			user = user.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			user = (await user).raw_text.replace(" ", "")
			cmd_check = f'cat /etc/xray/config.json | grep "{user}"'
			if subprocess.call(cmd_check, shell=True) == 0:
				await event.respond("**Username sudah ada. Silakan masukkan username baru.**", buttons=[
[Button.inline("🔄 Create Ulang","create-trojan")],
[Button.inline("❌ Cancel","trojan")]])
				return  # Keluar dari fungsi jika username sudah ada
		async with bot.conversation(chat) as limit_ip:
			await event.respond("🌐 **Limit IP:**")
			limit_ip = limit_ip.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			limit_ip = (await limit_ip).raw_text
			if not limit_ip.isdigit():
				await event.respond("🌐 **Limit IP harus berupa angka.**", buttons=[
[Button.inline("🔄 Create Ulang","create-trojan")],
[Button.inline("❌ Cancel","trojan")]])
				return  # Keluar dari fungsi jika limit_ip bukan angka
		async with bot.conversation(chat) as pw:
			await event.respond("📦 **Quota:**")
			pw = pw.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			pw = (await pw).raw_text
			if not pw.isdigit():
				await event.respond("📦 **Quota harus berupa angka.**", buttons=[
[Button.inline("🔄 Create Ulang","create-trojan")],
[Button.inline("❌ Cancel","trojan")]])
				return  # Keluar dari fungsi jika pw bukan angka
		async with bot.conversation(chat) as exp:
			await event.respond("⏳ **Masaaktif:**")
			exp = exp.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			exp = (await exp).raw_text
			if not exp.isdigit():
				await event.respond("⏳ **Masaaktif harus berupa angka.**", buttons=[
[Button.inline("🔄 Create Ulang","create-trojan")],
[Button.inline("❌ Cancel","trojan")]])
				return  # Keluar dari fungsi jika exp bukan angka
		bug = ""
		cmd = f'printf "%s\n" "{user}" "{limit_ip}" "{pw}" "{exp}" "{bug}" | addtr'
		try:
			a = subprocess.check_output(cmd, shell=True).decode("utf-8")
		except:
			await event.respond("**User Already Exist**")
		else:
			inline=[[Button.inline("‹ Back ›","trojan")]]
			today = DT.date.today()
			later = today + DT.timedelta(days=int(exp))
			b = [x.group() for x in re.finditer("trojan://(.*)",a)]
			print(b)
			uuid = re.search("trojan://(.*?)@",b[0]).group(1)
			msg = f"""
**◇━━━━━━━━━━◇**
		**⚡️ Xray/Trojan Account ⚡️**
**◇━━━━━━━━━━◇**
**» Remarks     :** `{user}`
**» Limit IP    :** `{limit_ip}`
**» Host Server :** `{DOMAIN}`
**» User Quota  :** `{pw} GB`
**» Port DNS    :** `443, 53`
**» port TLS    :** `222-1000`
**» User ID     :** `{uuid}`
**◇━━━━━━━━━━◇**
**» Link WS    :** 
```{b[0].replace(" ","")}```
**◇━━━━━━━━━━◇**
**» Link GRPC  :** 
```{b[2].replace(" ","")}```
**◇━━━━━━━━━━◇**
**» Format OpenClash :** 
https://{DOMAIN}:81/trojan-{user}.txt
**◇━━━━━━━━━━◇**
**Expired Until:** `{later}`
**» 🤖@WendiVpn**
"""
			await event.respond(msg,buttons=inline)
	chat = event.chat_id
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await create_trojan_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)

@bot.on(events.CallbackQuery(data=b'auto-trojan'))
async def create_trojan(event):
	async def create_trojan_(event):
		async with bot.conversation(chat) as limit_ip:
			await event.respond("🌐 **Limit IP:**")
			limit_ip = limit_ip.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			limit_ip = (await limit_ip).raw_text
			if not limit_ip.isdigit():
				await event.respond("🌐 **Limit IP harus berupa angka.**", buttons=[
[Button.inline("🔄 Create Ulang","create-trojan")],
[Button.inline("❌ Cancel","trojan")]])
				return  # Keluar dari fungsi jika limit_ip bukan angka
		async with bot.conversation(chat) as pw:
			await event.respond("📦 **Quota:**")
			pw = pw.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			pw = (await pw).raw_text
			if not pw.isdigit():
				await event.respond("📦 **Quota harus berupa angka.**", buttons=[
[Button.inline("🔄 Create Ulang","create-trojan")],
[Button.inline("❌ Cancel","trojan")]])
				return  # Keluar dari fungsi jika pw bukan angka
		async with bot.conversation(chat) as exp:
			await event.respond("⏳ **Masaaktif:**")
			exp = exp.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			exp = (await exp).raw_text
			if not exp.isdigit():
				await event.respond("⏳ **Masaaktif harus berupa angka.**", buttons=[
[Button.inline("🔄 Create Ulang","create-trojan")],
[Button.inline("❌ Cancel","trojan")]])
				return  # Keluar dari fungsi jika exp bukan angka
		bug = ""
		user = "TrojanPrem"+str(random.randint(100,1000))
		cmd_check = f'cat /etc/xray/config.json | grep "{user}"'
		if subprocess.call(cmd_check, shell=True) == 0:
			await event.respond("**Username Eror Coba Ulangi.**", buttons=[
[Button.inline("🔄 Ulangi Auto Name","auto-trojan")],
[Button.inline("❌ Cancel","trojan")]])
			return  # Keluar dari fung
		cmd = f'printf "%s\n" "{user}" "{limit_ip}" "{pw}" "{exp}" "{bug}" | addtr'
		try:
			a = subprocess.check_output(cmd, shell=True).decode("utf-8")
		except:
			await event.respond("**User Already Exist**")
		else:
			inline=[[Button.inline("‹ Back ›","trojan")]]
			today = DT.date.today()
			later = today + DT.timedelta(days=int(exp))
			b = [x.group() for x in re.finditer("trojan://(.*)",a)]
			print(b)
			uuid = re.search("trojan://(.*?)@",b[0]).group(1)
			msg = f"""
**◇━━━━━━━━━━◇**
		**⚡️ Xray/Trojan Account ⚡️**
**◇━━━━━━━━━━◇**
**» Remarks     :** `{user}`
**» Limit IP    :** `{limit_ip}`
**» Host Server :** `{DOMAIN}`
**» User Quota  :** `{pw} GB`
**» Port DNS    :** `443, 53`
**» port TLS    :** `222-1000`
**» User ID     :** `{uuid}`
**◇━━━━━━━━━━◇**
**» Link WS    :** 
```{b[0].replace(" ","")}```
**◇━━━━━━━━━━◇**
**» Link GRPC  :** 
```{b[2].replace(" ","")}```
**◇━━━━━━━━━━◇**
**» Format OpenClash :** 
https://{DOMAIN}:81/trojan-{user}.txt
**◇━━━━━━━━━━◇**
**Expired Until:** `{later}`
**» 🤖@WendiVpn**
"""
			await event.respond(msg,buttons=inline)
	chat = event.chat_id
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await create_trojan_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)

@bot.on(events.CallbackQuery(data=b'cek-trojan'))
async def cek_trojan(event):
	async def cek_trojan_(event):
		cmd = 'bot-cek-tr'.strip()
		x = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
		print(x)
		z = subprocess.check_output(cmd, shell=True).decode("utf-8")
		await event.respond(f"""
**◇━━━━━━━━━━◇**
	** ⟨🔸 Trojan Logged🔸⟩**
**◇━━━━━━━━━━◇**
```					  
{z}
```
**Shows Logged In Users Trojan**
**» 🤖@WendiVpn**
""",buttons=[[Button.inline("‹ Back ›","trojan")]])
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await cek_trojan_(event)
	else:
		await event.answer("Access Denied",alert=True)

@bot.on(events.CallbackQuery(data=b'trial-trojan'))
async def trial_trojan(event):
	async def trial_trojan_(event):
		async with bot.conversation(chat) as exp:
			await event.respond("**Choose Expiry Minutes**",buttons=[
[Button.inline(" 10 Menit ","10"),
Button.inline(" 15 Menit ","15")],
[Button.inline(" 30 Menit ","30"),
Button.inline(" 60 Menit ","60")]])
			exp = exp.wait_event(events.CallbackQuery)
			exp = (await exp).data.decode("ascii")
		cmd = f'printf "%s\n" "{exp}" | trialtr'
		try:
			a = subprocess.check_output(cmd, shell=True).decode("utf-8")
		except:
			await event.respond("**User Already Exist**")
		else:
			inline=[[Button.inline("‹ Back ›","trojan")]]
			#today = DT.date.today()
			#later = today + DT.timedelta(days=int(exp))
			b = [x.group() for x in re.finditer("trojan://(.*)",a)]
			print(b)
			remarks = re.search("#(.*)",b[0]).group(1)
			uuid = re.search("trojan://(.*?)@",b[0]).group(1)
			msg = f"""
**◇━━━━━━━━━━◇**
		**⚡️ Xray/Trojan Account ⚡️**
**◇━━━━━━━━━━◇**
**» Remarks     :** `{remarks}`
**» Host Server :** `{DOMAIN}`
**» User Quota  :** `Unlimited`
**» Port DNS    :** `443, 53`
**» port TLS    :** `222-1000`
**» Path Trojan :** `(/multi path)/trojan-ws`
**» User ID     :** `{uuid}`
**◇━━━━━━━━━━◇**
**» Link WS    :** 
```{b[0].replace(" ","")}```
**◇━━━━━━━━━━◇**
**» Link GRPC  :** 
```{b[2].replace(" ","")}```
**◇━━━━━━━━━━◇**
**» Format OpenClash :** 
https://{DOMAIN}:81/trojan-{remarks}.txt
**◇━━━━━━━━━━◇**
**» Expired Until:** `{exp} Minutes`
**» 🤖@WendiVpn**
"""
			await event.respond(msg,buttons=inline)
	chat = event.chat_id
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await trial_trojan_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)

@bot.on(events.CallbackQuery(data=b'delete-trojan'))
async def delete_trojan(event):
	async def delete_trojan_(event):
		cmd = 'cat /etc/xray/config.json | grep "^#!" | cut -d " " -f 2-3 | sort | uniq | nl'.strip()
		x = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
		print(x)
		z = subprocess.check_output(cmd, shell=True).decode("utf-8")
		await event.respond(f"""
**◇━━━━━━━━━━◇**
	** ⟨🔸 Trojan Account🔸⟩**
**◇━━━━━━━━━━◇**
```
{z}
```
""")
		async with bot.conversation(chat) as user:
			await event.respond(' **🔡Username:**')
			user = user.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			user = (await user).raw_text.replace(" ", "")
			cmd_check = f'cat /etc/xray/config.json | grep "{user}"'
			if subprocess.call(cmd_check, shell=True) != 0:
				await event.respond("**Username tidak ditemukan. Silakan masukkan username yang benar.**", buttons=[
[Button.inline("🔄 Delet Ulang","delete-trojan")],
[Button.inline("❌ Cancel","trojan")]])
				return
			cmd = f'printf "%s\n" "{user}" | deltr'
		try:
			a = subprocess.check_output(cmd, shell=True).decode("utf-8")
		except subprocess.CalledProcessError:  # Menangani kesalahan jika user tidak ada
			await event.respond(f" **Successfully**", buttons=[[Button.inline("‹ Back ›","trojan")]])
		else:
			await event.respond(f" **Successfully Delet**", buttons=[[Button.inline("‹ Back ›","trojan")]])
	chat = event.chat_id
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await delete_trojan_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)

@bot.on(events.CallbackQuery(data=b'bot-member-trojan'))
async def bot_member_trojan(event):
	async def bot_member_trojan_(event):
		cmd = 'cat /etc/xray/config.json | grep "^#!" | cut -d " " -f 2-3 | sort | uniq | nl'.strip()
		x = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
		print(x)
		z = subprocess.check_output(cmd, shell=True).decode("utf-8")
		await event.respond(f"""
**◇━━━━━━━━━━◇**
	** ⟨🔸 Trojan Account🔸⟩**
**◇━━━━━━━━━━◇**
```
{z}
```
**Menampilkan Member Trojan**
**» 🤖@WendiVpn**
""",buttons=[[Button.inline("‹ Back ›","trojan")]])
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await bot_member_trojan_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)

@bot.on(events.CallbackQuery(data=b'renew-tr'))
async def renew_tr(event):
	async def renew_tr_(event):
		cmd = 'cat /etc/xray/config.json | grep "^#!" | cut -d " " -f 2-3 | sort | uniq | nl'.strip()
		x = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
		print(x)
		z = subprocess.check_output(cmd, shell=True).decode("utf-8")
		await event.respond(f"""
**◇━━━━━━━━━━◇**
	** ⟨🔸 Trojan Account🔸⟩**
**◇━━━━━━━━━━◇**
```
{z}
```
""")
		async with bot.conversation(chat) as user:
			await event.respond(' **🔡Username Renew:**')
			user = user.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			user = (await user).raw_text.replace(" ", "")
			cmd_check = f'cat /etc/xray/config.json | grep "{user}"'
			if subprocess.call(cmd_check, shell=True) != 0:
				await event.respond("**Username tidak ditemukan. Silakan masukkan username yang benar.**", buttons=[
[Button.inline("🔄 Renew Ulang","renew-tr")],
[Button.inline("❌ Cancel","trojan")]])
				return
		async with bot.conversation(chat) as exp:
			await event.respond(' **Ubah Masaaktif:**')
			exp = exp.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			exp = (await exp).raw_text
			if not exp.isdigit():
				await event.respond(" **Masaaktif harus berupa angka.**", buttons=[
[Button.inline("🔄 Renew Ulang","renew-tr")],
[Button.inline("❌ Cancel","trojan")]])
				return  # Keluar dari fungsi jika exp bukan angka
		async with bot.conversation(chat) as quota:
			await event.respond(' **Limit Quota:**')
			quota = quota.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			quota = (await quota).raw_text
			if not quota.isdigit():
				await event.respond(" **Limit Quota harus berupa angka.**", buttons=[
[Button.inline("🔄 Renew Ulang","renew-tr")],
[Button.inline("❌ Cancel","trojan")]])
				return  # Keluar dari fungsi jika quota bukan angka
		async with bot.conversation(chat) as ip:
			await event.respond(' **Limit Ip:**')
			ip = ip.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			ip = (await ip).raw_text
			if not ip.isdigit():
				await event.respond(" **Limit Ip harus berupa angka.**", buttons=[
[Button.inline("🔄 Renew Ulang","renew-tr")],
[Button.inline("❌ Cancel","trojan")]])
				return  # Keluar dari fungsi jika ip bukan angka
			cmd = f'printf "%s\n" "{user}" "{exp}" "{quota}" "{ip}" | renewtr'
		try:
			a = subprocess.check_output(cmd, shell=True).decode("utf-8")
		except:
			await event.respond(f"**User** `{user}` **Successfully**",buttons=[[Button.inline("‹ Back ›","trojan")]])
		else:
			await event.respond(f"**Successfully Renew** `{user}`",buttons=[[Button.inline("‹ Back ›","trojan")]])
	chat = event.chat_id
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await renew_tr_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)


@bot.on(events.CallbackQuery(data=b'trojan'))
async def trojan(event):
	async def trojan_(event):
		inline = [
[Button.inline("⚡️Auto Trojan⚡️","auto-trojan")],
[Button.inline(" ☣️Trial Trojan ","trial-trojan"),
Button.inline(" ➕Create Trojan ","create-trojan")],
[Button.inline(" 👤Member Trojan ","bot-member-trojan"),
Button.inline(" ♻️Renew Trojan ","renew-tr")],
[Button.inline(" ✅Check Trojan ","cek-trojan"),
Button.inline(" ❌Delete Trojan ","delete-trojan")],
[Button.inline(" 🔒Lock Trojan ","lock-trojan"),
Button.inline(" 🔐Unlock Trojan ","unlock-trojan")],
[Button.inline(" 📝Detail Trojan ","d-trojan")],
[Button.inline("‹ Back ›","menu")]]
		z = requests.get(f"http://ip-api.com/json/?fields=country,region,city,timezone,isp").json()
		tr = f' cat /etc/trojan/.trojan.db | grep "###" | wc -l'
		trj = subprocess. check_output(tr, shell=True).decode("ascii")
		username = sender.username
		user_id = sender.id
		msg = f"""
**◇━━━━━━━━━━◇**
**⚡️ TROJAN MANAGER ⚡️**
**◇━━━━━━━━━━◇**
**»🔰Service:** `TROJAN`
**»🔰Jumlah TROJAN :** `{trj.strip()}` __account__
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
		await trojan_(event)
	else:
		await event.answer("Access Denied",alert=True)
