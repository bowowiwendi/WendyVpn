from kyt import *

#LOCK ss
@bot.on(events.CallbackQuery(data=b'lock-ss'))
async def lock_ss(event):
	async def lock_ss_(event):
		cmd = 'cat /etc/xray/config.json | grep "^#!!" | cut -d " " -f 2-3 | sort | uniq | nl'.strip()
		x = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
		print(x)
		z = subprocess.check_output(cmd, shell=True).decode("utf-8")
		await event.respond(f"""
**◇━━━━━━━━━━◇**
	** ⟨🔸 SS Account🔸⟩**
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
[Button.inline("🔄 Lock Ulang","lock-ss")],
[Button.inline("❌ Cancel","shadowsocks")]])
				return
			cmd = f'printf "%s\n" "{user}" | lock-ss'
		try:
			a = subprocess.check_output(cmd, shell=True).decode("utf-8")
		except subprocess.CalledProcessError:  # Menangani kesalahan jika user tidak ada
			await event.respond(f" **Successfully**", buttons=[[Button.inline("‹ Back ›","shadowsocks")]])
		else:
			await event.respond(f" **Successfully Lock**", buttons=[[Button.inline("‹ Back ›","shadowsocks")]])
	chat = event.chat_id
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await lock_ss_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)
#UNLOCK ss
@bot.on(events.CallbackQuery(data=b'unlock-ss'))
async def unlock_ss(event):
	async def unlock_ss_(event):
		cmd = 'cat /etc/xray/.lock.db | grep "^#!!" | cut -d " " -f 2-3 | sort | uniq | nl'.strip()
		x = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
		print(x)
		z = subprocess.check_output(cmd, shell=True).decode("utf-8")
		await event.respond(f"""
**◇━━━━━━━━━━◇**
	** ⟨🔸 SS Account🔸⟩**
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
[Button.inline("🔄 Unlock Ulang","unlock-ss")],
[Button.inline("❌ Cancel","shadowsocks")]])
				return  # Keluar dari fungsi jika username tidak ditemukan
			cmd = f'printf "%s\n" "{user}" | unlock-ss'
		try:
			a = subprocess.check_output(cmd, shell=True).decode("utf-8")
		except subprocess.CalledProcessError:  # Menangani kesalahan jika user tidak ada
			await event.respond(f" **Successfully**", buttons=[[Button.inline("‹ Back ›","shadowsocks")]])
		else:
			await event.respond(f" **Successfully Unlock**", buttons=[[Button.inline("‹ Back ›","shadowsocks")]])
	chat = event.chat_id
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await unlock_ss_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)
#detail
@bot.on(events.CallbackQuery(data=b'd-ss'))
async def l_ss(event):
	async def l_ss_(event):
		cmd = 'cat /etc/xray/config.json | grep "^#!!" | cut -d " " -f 2-3 | sort | uniq | nl'.strip()
		x = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
		print(x)
		z = subprocess.check_output(cmd, shell=True).decode("utf-8")
		await event.respond(f"""
**◇━━━━━━━━━━◇**
	** ⟨🔸 Sadowsocks Account🔸⟩**
**◇━━━━━━━━━━◇**
```
{z}
```
""")
		async with bot.conversation(chat) as user:
			await event.respond(" **🔡Username:**")
			user = exp.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			user = (await user).raw_text.replace(" ", "")
			cmd_check = f'cat /etc/xray/config.json | grep "{user}"'
			if subprocess.call(cmd_check, shell=True) != 0:
				await event.respond("**Username tidak ditemukan. Silakan masukkan username yang benar.**", buttons=[
[Button.inline("🔄 Ulangi","d-ss")],
[Button.inline("❌ Cancel","shadowsocks")]])
				return
			cmd = f'cat /var/www/html/sodosokws-{user}.txt'.strip()
			x = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
			print(x)
			z = subprocess.check_output(cmd, shell=True).decode("utf-8")
			if z:
				await event.respond(f"""
**◇━━━━━━━━━━◇**
	** ⟨🔸 Sadowsocks Account🔸⟩**
**◇━━━━━━━━━━◇**
```
{z}
```
""",buttons=[[Button.inline("‹ Back ›","shadowsocks")]])
			else:
				await event.respond("**Filed**: User tidak ditemukan", buttons=[[Button.inline("‹ Back ›","shadowsocks")]])
	chat = event.chat_id
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await l_ss_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)

@bot.on(events.CallbackQuery(data=b'create-shadowsocks'))
async def create_shadowsocks(event):
	async def create_shadowsocks_(event):
		async with bot.conversation(chat) as user:
			await event.respond('🔡**Username:**')
			user = user.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			user = (await user).raw_text.replace(" ", "")
			cmd_check = f'cat /etc/xray/config.json | grep "{user}"'
			if subprocess.call(cmd_check, shell=True) == 0:
				await event.respond("**Username sudah ada. Silakan masukkan username baru.**", buttons=[
[Button.inline("🔄 Create Ulang","create-shadowsocks")],
[Button.inline("❌ Cancel","shadowsocks")]])
				return  # Keluar dari fungsi jika username sudah ada
		async with bot.conversation(chat) as limit_ip:
			await event.respond("🌐 **Limit IP:**")
			limit_ip = limit_ip.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			limit_ip = (await limit_ip).raw_text
			if not limit_ip.isdigit():
				await event.respond("🌐 **Limit IP harus berupa angka.**", buttons=[
[Button.inline("🔄 Create Ulang","create-shadowsocks")],
[Button.inline("❌ Cancel","shadowsocks")]])
				return  # Keluar dari fungsi jika limit_ip bukan angka
		async with bot.conversation(chat) as pw:
			await event.respond("📦 **Quota:**")
			pw = pw.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			pw = (await pw).raw_text
			if not pw.isdigit():
				await event.respond("📦 **Quota harus berupa angka.**", buttons=[
[Button.inline("🔄 Create Ulang","create-shadowsocks")],
[Button.inline("❌ Cancel","shadowsocks")]])
				return  # Keluar dari fungsi jika pw bukan angka
		async with bot.conversation(chat) as exp:
			await event.respond("⏳ **Masaaktif:**")
			exp = exp.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			exp = (await exp).raw_text
			if not exp.isdigit():
				await event.respond("⏳ **Masaaktif harus berupa angka.**", buttons=[
[Button.inline("🔄 Create Ulang","create-shadowsocks")],
[Button.inline("❌ Cancel","shadowsocks")]])
				return  # Keluar dari fungsi jika exp bukan angka
		bug = ""
		cmd = f'printf "%s\n" "{user}" "{limit_ip}" "{exp}" "{pw}" "{bug}" | addss'
		try:
			a = subprocess.check_output(cmd, shell=True).decode("utf-8")
		except:
			await event.respond("**User Already Exist**")
		else:
			inline=[[Button.inline("‹ Back ›","menu")]]
			today = DT.date.today()
			later = today + DT.timedelta(days=int(exp))
			x = [x.group() for x in re.finditer("ss://(.*)",a)]
			print(x)
			# remarks = re.search("#(.*)",x[0]).group(1)
			# domain = re.search("@(.*?):",x[0]).group(1)
			uuid = re.search("ss://(.*?)@",x[0]).group(1)
			# path = re.search("path=(.*)&",x[0]).group(1)
			msg = f"""
**◇━━━━━━━━━━◇**
			**⚡️ Xray/SS Account ⚡️**
**◇━━━━━━━━━━◇**
**» Remarks     :** `{user}`
**» Host Server :** `{DOMAIN}`
**» Limit IP    :** `{limit_ip}`
**» User Quota  :** `Unlimited`
**» Password    :** `{uuid}`
**» Cipers      :** `aes-128-gcm`
**» NetWork     :** `(WS) or (gRPC)`
**» Path        :** `(/multi path)/ss-ws`
**» ServiceName :** `ss-grpc`
**◇━━━━━━━━━━◇**
**» Link TLS    :**
```{x[0]}```
**◇━━━━━━━━━━◇**
**» Link gRPC   :** 
```{x[2].replace(" ","")}```
**◇━━━━━━━━━━◇**
**» Link JSON  :** 
https://${DOMAIN}:81/oc-sodosokws-{user}.txt
**◇━━━━━━━━━━◇**
**» Expired Until:** `{later}`
**» 🤖@WendiVpn**
"""
			await event.respond(msg,buttons=inline)
	chat = event.chat_id
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await create_shadowsocks_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)

@bot.on(events.CallbackQuery(data=b'auto-shadowsocks'))
async def create_shadowsocks(event):
	async def create_shadowsocks_(event):
		async with bot.conversation(chat) as limit_ip:
			await event.respond("🌐 **Limit IP:**")
			limit_ip = limit_ip.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			limit_ip = (await limit_ip).raw_text
			if not limit_ip.isdigit():
				await event.respond("🌐 **Limit IP harus berupa angka.**", buttons=[
[Button.inline("🔄 Auto Ulang","auto-shadowsocks")],
[Button.inline("❌ Cancel","shadowsocks")]])
				return  # Keluar dari fungsi jika limit_ip bukan angka
		async with bot.conversation(chat) as pw:
			await event.respond("📦 **Quota:**")
			pw = pw.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			pw = (await pw).raw_text
			if not pw.isdigit():
				await event.respond("📦 **Quota harus berupa angka.**", buttons=[
[Button.inline("🔄 Auto Ulang","auto-shadowsocks")],
[Button.inline("❌ Cancel","shadowsocks")]])
				return  # Keluar dari fungsi jika pw bukan angka
		async with bot.conversation(chat) as exp:
			await event.respond("⏳ **Masaaktif:**")
			exp = exp.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			exp = (await exp).raw_text
			if not exp.isdigit():
				await event.respond("⏳ **Masaaktif harus berupa angka.**", buttons=[
[Button.inline("🔄 Auto Ulang","create-shadowsocks")],
[Button.inline("❌ Cancel","shadowsocks")]])
				return  # Keluar dari fungsi jika exp bukan angka
		bug = ""
		user = "ShadowPrem"+str(random.randint(100,1000))
		cmd_check = f'cat /etc/xray/config.json | grep "{user}"'
		if subprocess.call(cmd_check, shell=True) == 0:
			await event.respond("**Username Eror Coba Ulangi.**", buttons=[
[Button.inline("🔄 Ulangi Auto Name","auto-shadowsocks")],
[Button.inline("❌ Cancel","shadowsocks")]])
			return  # Keluar dari fung
		cmd = f'printf "%s\n" "{user}" "{limit_ip}" "{exp}" "{pw}" "{bug}" | addss'
		try:
			a = subprocess.check_output(cmd, shell=True).decode("utf-8")
		except:
			await event.respond("**User Already Exist**")
		else:
			inline=[[Button.inline("‹ Back ›","menu")]]
			today = DT.date.today()
			later = today + DT.timedelta(days=int(exp))
			x = [x.group() for x in re.finditer("ss://(.*)",a)]
			print(x)
			# remarks = re.search("#(.*)",x[0]).group(1)
			# domain = re.search("@(.*?):",x[0]).group(1)
			uuid = re.search("ss://(.*?)@",x[0]).group(1)
			# path = re.search("path=(.*)&",x[0]).group(1)
			msg = f"""
**◇━━━━━━━━━━◇**
			**⚡️ Xray/SS Account ⚡️**
**◇━━━━━━━━━━◇**
**» Remarks     :** `{user}`
**» Host Server :** `{DOMAIN}`
**» Limit IP    :** `{limit_ip}`
**» User Quota  :** `Unlimited`
**» Password    :** `{uuid}`
**» Cipers      :** `aes-128-gcm`
**» NetWork     :** `(WS) or (gRPC)`
**» Path        :** `(/multi path)/ss-ws`
**» ServiceName :** `ss-grpc`
**◇━━━━━━━━━━◇**
**» Link TLS    :**
```{x[0]}```
**◇━━━━━━━━━━◇**
**» Link gRPC   :** 
```{x[2].replace(" ","")}```
**◇━━━━━━━━━━◇**
**» Link JSON  :** 
https://${DOMAIN}:81/oc-sodosokws-{user}.txt
**◇━━━━━━━━━━◇**
**» Expired Until:** `{later}`
**» 🤖@WendiVpn**
"""
			await event.respond(msg,buttons=inline)
	chat = event.chat_id
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await create_shadowsocks_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)

@bot.on(events.CallbackQuery(data=b'cek-shadowsocks'))
async def cek_shadowsocks(event):
	async def cek_shadowsocks_(event):
		cmd = 'bot-cek-ss'.strip()
		x = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
		print(x)
		z = subprocess.check_output(cmd, shell=True).decode("utf-8")
		await event.respond(f"""
**◇━━━━━━━━━━◇**
	** ⟨🔸 Shadowsocks Logged🔸⟩**
**◇━━━━━━━━━━◇**
```					  
{z}
```
**Shows Logged In Users Shadowsocks**
**» 🤖@WendiVpn**
""",buttons=[[Button.inline("‹ Back ›","menu")]])
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await cek_shadowsocks_(event)
	else:
		await event.answer("Access Denied",alert=True)

@bot.on(events.CallbackQuery(data=b'delete-shadowsocks'))
async def delete_shadowsocks(event):
	async def delete_shadowsocks_(event):
		cmd = 'cat /etc/xray/config.json | grep "^#!!" | cut -d " " -f 2-3 | sort | uniq | nl'.strip()
		x = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
		print(x)
		z = subprocess.check_output(cmd, shell=True).decode("utf-8")
		await event.respond(f"""
**◇━━━━━━━━━━◇**
	** ⟨🔸 Sadowsocks Account🔸⟩**
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
[Button.inline("🔄 Delet Ulang","delete-shadowsocks")],
[Button.inline("❌ Cancel","shadowsocks")]])
				return
			cmd = f'printf "%s\n" "{user}" | delss'
		try:
			a = subprocess.check_output(cmd, shell=True).decode("utf-8")
		except:
			await event.respond(f"**User** `{user}` **Successfully Deleted**",buttons=[[Button.inline("‹ Back ›","shadowsocks")]])
		else:
			inline=[[Button.inline("‹ Back ›","shadowsocks")]]
			msg = f"""**Successfully Deleted**"""
			await event.respond(msg,buttons=inline)
	chat = event.chat_id
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await delete_shadowsocks_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)

@bot.on(events.CallbackQuery(data=b'trial-shadowsocks'))
async def trial_shadowsocks(event):
	async def trial_shadowsocks_(event):
		async with bot.conversation(chat) as exp:
			await event.respond("**Choose Expiry Minutes**",buttons=[
[Button.inline(" 10 Menit ","10"),
Button.inline(" 15 Menit ","15")],
[Button.inline(" 30 Menit ","30"),
Button.inline(" 60 Menit ","60")]])
			exp = exp.wait_event(events.CallbackQuery)
			exp = (await exp).data.decode("ascii")
		cmd = f'printf "%s\n" "{exp}" | trialss'
		try:
			a = subprocess.check_output(cmd, shell=True).decode("utf-8")
		except:
			await event.respond("**User Already Exist**")
		else:
			inline=[[Button.inline("‹ Back ›","menu")]]
			#today = DT.date.today()
			#later = today + DT.timedelta(days=int(exp))
			x = [x.group() for x in re.finditer("ss://(.*)",a)]
			print(x)
			remarks = re.search("#(.*)",x[0]).group(1)
			# domain = re.search("@(.*?):",x[0]).group(1)
			uuid = re.search("ss://(.*?)@",x[0]).group(1)
			# path = re.search("path=(.*)&",x[0]).group(1)
			msg = f"""
**◇━━━━━━━━━━◇**
			**⚡️ Xray/SS Account ⚡️**
**◇━━━━━━━━━━◇**
**» Remarks     :** `{remarks}`
**» Host Server :** `{DOMAIN}`
**» User Quota  :** `Unlimited`
**» Password    :** `{uuid}`
**» NetWork     :** `(WS) or (gRPC)`
**» Path        :** `(/multi path)/ss-ws`
**» ServiceName :** `ss-grpc`
**◇━━━━━━━━━━◇**
**» Link TLS    :**
```{x[0]}```
**◇━━━━━━━━━━◇**
**» Link gRPC   :** 
```{x[2].replace(" ","")}```
**◇━━━━━━━━━━◇**
**» Link JSON  :** 
`https://${DOMAIN}:81/ss-{remarks}.txt`
**◇━━━━━━━━━━◇**
**» Expired Until :** `{exp} Minutes`
**» 🤖@WendiVpn**
"""
			await event.respond(msg,buttons=inline)
	chat = event.chat_id
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await trial_shadowsocks_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)

@bot.on(events.CallbackQuery(data=b'bot-member-ss'))
async def bot_member_ss(event):
	async def bot_member_ss_(event):
		cmd = 'cat /etc/xray/config.json | grep "^#!!" | cut -d " " -f 2-3 | sort | uniq | nl'.strip()
		x = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
		print(x)
		z = subprocess.check_output(cmd, shell=True).decode("utf-8")
		await event.respond(f"""
**◇━━━━━━━━━━◇**
	** ⟨🔸 Sadowsocks Account🔸⟩**
**◇━━━━━━━━━━◇**
```
{z}
```
**Menampilkan Member Sadowsocks**
**» 🤖@WendiVpn**
""",buttons=[[Button.inline("‹ Menu Utama ›","menu")]])
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await bot_member_ss_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)

@bot.on(events.CallbackQuery(data=b'renew-ss'))
async def renew_ss(event):
	async def renew_ss_(event):
		cmd = 'cat /etc/xray/config.json | grep "^#!!" | cut -d " " -f 2-3 | sort | uniq | nl'.strip()
		x = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
		print(x)
		z = subprocess.check_output(cmd, shell=True).decode("utf-8")
		await event.respond(f"""
**◇━━━━━━━━━━◇**
	** ⟨🔸 Sadowsocks Account🔸⟩**
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
[Button.inline("🔄 Renew Ulang","renew-ss")],
[Button.inline("❌ Cancel","shadowsocks")]])
				return
		async with bot.conversation(chat) as exp:
			await event.respond(' **Ubah Masaaktif:**')
			exp = exp.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			exp = (await exp).raw_text
			if not exp.isdigit():
				await event.respond(" **Masaaktif harus berupa angka.**", buttons=[
[Button.inline("🔄 Renew Ulang","renew-ss")],
[Button.inline("❌ Cancel","shadowsocks")]])
				return  # Keluar dari fungsi jika exp bukan angka
			cmd = f'printf "%s\n" "{user}" "{exp}" | renewss'
		try:
			a = subprocess.check_output(cmd, shell=True).decode("utf-8")
		except:
			await event.respond(f"**User** `{user}` **Not Found**",buttons=[[Button.inline("‹ Menu Utama ›","menu")]])
		else:
			await event.respond(f"**Successfully Renew** `{user}`",buttons=[[Button.inline("‹ Menu Utama ›","menu")]])
	chat = event.chat_id
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await renew_ss_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)


@bot.on(events.CallbackQuery(data=b'shadowsocks'))
async def shadowsocks(event):
	async def shadowsocks_(event):
		inline = [
[Button.inline("⚡️Auto SS⚡️","auto-shadowsocks")],
[Button.inline(" ☣️Trial SS ","trial-shadowsocks"),
Button.inline(" ➕Create SS ","create-shadowsocks")],
[Button.inline(" 👤Member SS ","bot-member-ss"),
Button.inline(" ♻️Renew SS ","renew-ss")],
[Button.inline(" ✅Check SS ","cek-shadowsocks"),
Button.inline(" ❌Delete SS ","delete-shadowsocks")],
[Button.inline("🔒Lock SS","lock-ss"),
Button.inline("🔐Unlock SS","unlock-ss")],
[Button.inline(" 📝Detail SS ","d-ss")],
[Button.inline("‹ Back ›","menu")]]
		z = requests.get(f"http://ip-api.com/json/?fields=country,region,city,timezone,isp").json()
		ss = f' cat /etc/shadowsocks/.shadowsocks.db | grep "###" | wc -l'
		ssk = subprocess. check_output(ss, shell=True).decode("ascii")
		username = sender.username
		user_id = sender.id
		msg = f"""
**◇━━━━━━━━━━◇**
**⚡️ SHDWSK MANAGER ⚡️**
**◇━━━━━━━━━━◇**
**»🔰Service:** `SHADOWSOCKS`
**»🔰Jumlah SHADOWSOCKS:** `{ssk.strip()}` __account__
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
		await shadowsocks_(event)
	else:
		await event.answer("Access Denied",alert=True)
