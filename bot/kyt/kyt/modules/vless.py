from kyt import *

#detail
@bot.on(events.CallbackQuery(data=b'd-vless'))
async def l_vless(event):
	async def l_vless_(event):
		cmd = 'cat /etc/xray/config.json | grep "^#&" | cut -d " " -f 2-3 | sort | uniq | nl'.strip()
		x = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
		print(x)
		z = subprocess.check_output(cmd, shell=True).decode("utf-8")
		await event.respond(f"""
**◇━━━━━━━━━━◇**
	** ⟨🔸 Vless Account🔸⟩**
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
[Button.inline("🔄 Ulangi","d-vless")],
[Button.inline("❌ Cancel","vless")]])
				return
			cmd = f'cat /var/www/html/vless-{user}.txt'.strip()
			x = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
			print(x)
			z = subprocess.check_output(cmd, shell=True).decode("utf-8")
			if z:
				await event.respond(f"""
**◇━━━━━━━━━━◇**
	** ⟨🔸 Vless Account🔸⟩**
**◇━━━━━━━━━━◇**
```
{z}
```
""",buttons=[[Button.inline("‹ Back ›","vless")]])
			else:
				await event.respond("**Filed**: User tidak ditemukan", buttons=[[Button.inline("‹ Back ›","vless")]])
	chat = event.chat_id
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await l_vless_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)

#LOCK vless
@bot.on(events.CallbackQuery(data=b'lock-vless'))
async def lock_vless(event):
	async def lock_vless_(event):
		cmd = 'cat /etc/xray/config.json | grep "^#&" | cut -d " " -f 2-3 | sort | uniq | nl'.strip()
		x = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
		print(x)
		z = subprocess.check_output(cmd, shell=True).decode("utf-8")
		await event.respond(f"""
**◇━━━━━━━━━━◇**
	** ⟨🔸 Vless Account🔸⟩**
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
[Button.inline("🔄 Lock Ulang","lock-vless")],
[Button.inline("❌ Cancel","vless")]])
				return
			cmd = f'printf "%s\n" "{user}" | lock-vl'
		try:
			a = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
		except subprocess.CalledProcessError:  # Menangani kesalahan jika user tidak ada
			await event.respond(f" **Successfully**", buttons=[[Button.inline("‹ Back ›","vless")]])
		else:
			await event.respond(f" **Successfully Lock**", buttons=[[Button.inline("‹ Back ›","vless")]])
	chat = event.chat_id
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await lock_vless_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)
#UNLOCK vless
@bot.on(events.CallbackQuery(data=b'unlock-vless'))
async def unlock_vless(event):
	async def unlock_vless_(event):
		cmd = 'cat /etc/xray/.lock.db | grep "^#&" | cut -d " " -f 2-3 | sort | uniq | nl'.strip()
		x = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
		print(x)
		z = subprocess.check_output(cmd, shell=True).decode("utf-8")
		await event.respond(f"""
**◇━━━━━━━━━━◇**
	** ⟨🔸 Vless Account🔸⟩**
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
[Button.inline("🔄 Unlock Ulang","unlock-vless")],
[Button.inline("❌ Cancel","vless")]])
				return  # Keluar dari fungsi jika username tidak ditemukan
			cmd = f'printf "%s\n" "{user}" | unlock-vl'
		try:
			a = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
		except subprocess.CalledProcessError:  # Menangani kesalahan jika user tidak ada
			await event.respond(f" **Successfully**", buttons=[[Button.inline("‹ Back ›","vless")]])
		else:
			await event.respond(f" **Successfully Lock**", buttons=[[Button.inline("‹ Back ›","vless")]])
	chat = event.chat_id
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await unlock_vless_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)

@bot.on(events.CallbackQuery(data=b'create-vless'))
async def create_vless(event):
	async def create_vless_(event):
		async with bot.conversation(chat) as user:
			await event.respond('🔡**Username:**')
			user = user.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			user = (await user).raw_text.replace(" ", "")
			cmd_check = f'cat /etc/xray/config.json | grep "{user}"'
			if subprocess.call(cmd_check, shell=True) == 0:
				await event.respond("**Username sudah ada. Silakan masukkan username baru.**", buttons=[
[Button.inline("🔄 Create Ulang","create-vless")],
[Button.inline("❌ Cancel","vless")]])
				return  # Keluar dari fungsi jika username sudah ada
		async with bot.conversation(chat) as limit_ip:
			await event.respond("🌐 **Limit IP:**")
			limit_ip = limit_ip.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			limit_ip = (await limit_ip).raw_text
			if not limit_ip.isdigit():
				await event.respond("🌐 **Limit IP harus berupa angka.**", buttons=[
[Button.inline("🔄 Create Ulang","create-vless")],
[Button.inline("❌ Cancel","vless")]])
				return  # Keluar dari fungsi jika limit_ip bukan angka
		async with bot.conversation(chat) as pw:
			await event.respond("📦 **Quota:**")
			pw = pw.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			pw = (await pw).raw_text
			if not pw.isdigit():
				await event.respond("📦 **Quota harus berupa angka.**", buttons=[
[Button.inline("🔄 Create Ulang","create-vless")],
[Button.inline("❌ Cancel","vless")]])
				return  # Keluar dari fungsi jika pw bukan angka
		async with bot.conversation(chat) as exp:
			await event.respond("⏳ **Masaaktif:**")
			exp = exp.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			exp = (await exp).raw_text
			if not exp.isdigit():
				await event.respond("⏳ **Masaaktif harus berupa angka.**", buttons=[
[Button.inline("🔄 Create Ulang","create-vless")],
[Button.inline("❌ Cancel","vless")]])
				return  # Keluar dari fungsi jika exp bukan angka
		bug = ""
		cmd = f'printf "%s\n" "{user}" "{limit_ip}" "{pw}" "{exp}" "{bug}" | addvless'
		try:
			a = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
		except:
			await event.respond("**User Already Exist**")
		else:
			inline=[[Button.inline("‹ Back ›","vless")]]
			today = DT.date.today()
			later = today + DT.timedelta(days=int(exp))
			x = [x.group() for x in re.finditer("vless://(.*)",a)]
			print(x)
			# remarks = re.search("#(.*)",x[0]).group(1)
			# domain = re.search("@(.*?):",x[0]).group(1)
			uuid = re.search("vless://(.*?)@",x[0]).group(1)
			# path = re.search("path=(.*)&",x[0]).group(1)
			msg = f"""
**◇━━━━━━━━━━◇**
		**⚡️ Xray/Vless Account ⚡️**
**◇━━━━━━━━━━◇**
**» Remarks     :** `{user}`
**» Host Server :** `{DOMAIN}`
**» Limit IP    :** `{limit_ip}`
**» User Quota  :** `{pw} GB`
**» Port DNS    :** `443, 53`
**» port TLS    :** `222-1000`
**» Port NTLS   :** `80, 8080, 8081-9999`
**» NetWork     :** `(WS) or (gRPC)`
**» User ID     :** `{uuid}`
**» Path Vless  :** `(/multi path)/vless `
**» Path Dynamic:** `http://BUG.COM/vless `
**◇━━━━━━━━━━◇**
**» Link TLS   : **
```{x[0]}```
**◇━━━━━━━━━━◇**
**» Link GRPC  :**
```{x[2].replace(" ","")}```
**◇━━━━━━━━━━◇**
**» Format OpenClash :** 
https://{DOMAIN}:81/vless-{user}.txt
**◇━━━━━━━━━━◇**
**» Expired Until:** `{later}`
**» 🤖@WendiVpn**
"""
			await event.respond(msg,buttons=inline)
	chat = event.chat_id
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await create_vless_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)

@bot.on(events.CallbackQuery(data=b'auto-vless'))
async def create_vless(event):
	async def create_vless_(event):
		async with bot.conversation(chat) as limit_ip:
			await event.respond("🌐 **Limit IP:**")
			limit_ip = limit_ip.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			limit_ip = (await limit_ip).raw_text
			if not limit_ip.isdigit():
				await event.respond("🌐 **Limit IP harus berupa angka.**", buttons=[
[Button.inline("🔄 Create Ulang","create-vless")],
[Button.inline("❌ Cancel","vless")]])
				return  # Keluar dari fungsi jika limit_ip bukan angka
		async with bot.conversation(chat) as pw:
			await event.respond("📦 **Quota:**")
			pw = pw.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			pw = (await pw).raw_text
			if not pw.isdigit():
				await event.respond("📦 **Quota harus berupa angka.**", buttons=[
[Button.inline("🔄 Create Ulang","create-vless")],
[Button.inline("❌ Cancel","vless")]])
				return  # Keluar dari fungsi jika pw bukan angka
		async with bot.conversation(chat) as exp:
			await event.respond("⏳ **Masaaktif:**")
			exp = exp.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			exp = (await exp).raw_text
			if not exp.isdigit():
				await event.respond("⏳ **Masaaktif harus berupa angka.**", buttons=[
[Button.inline("🔄 Create Ulang","create-vless")],
[Button.inline("❌ Cancel","vless")]])
				return  # Keluar dari fungsi jika exp bukan angka
		bug = ""
		user = "VlessPrem"+str(random.randint(100,1000))
		cmd_check = f'cat /etc/xray/config.json | grep "{user}"'
		if subprocess.call(cmd_check, shell=True) == 0:
			await event.respond("**Username Eror Coba Ulangi.**", buttons=[
[Button.inline("🔄 Ulangi Auto Name","auto-vless")],
[Button.inline("❌ Cancel","vless")]])
			return  # Keluar dari fung
		cmd = f'printf "%s\n" "{user}" "{limit_ip}" "{pw}" "{exp}" "{bug}" | addvless'
		try:
			a = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
		except:
			await event.respond("**User Already Exist**")
		else:
			inline=[[Button.inline("‹ Back ›","vless")]]
			today = DT.date.today()
			later = today + DT.timedelta(days=int(exp))
			x = [x.group() for x in re.finditer("vless://(.*)",a)]
			print(x)
			# remarks = re.search("#(.*)",x[0]).group(1)
			# domain = re.search("@(.*?):",x[0]).group(1)
			uuid = re.search("vless://(.*?)@",x[0]).group(1)
			# path = re.search("path=(.*)&",x[0]).group(1)
			msg = f"""
**◇━━━━━━━━━━◇**
		**⚡️ Xray/Vless Account ⚡️**
**◇━━━━━━━━━━◇**
**» Remarks     :** `{user}`
**» Host Server :** `{DOMAIN}`
**» Limit IP    :** `{limit_ip}`
**» User Quota  :** `{pw} GB`
**» Port DNS    :** `443, 53`
**» port TLS    :** `222-1000`
**» Port NTLS   :** `80, 8080, 8081-9999`
**» NetWork     :** `(WS) or (gRPC)`
**» User ID     :** `{uuid}`
**» Path Vless  :** `(/multi path)/vless `
**» Path Dynamic:** `http://BUG.COM/vless `
**◇━━━━━━━━━━◇**
**» Link TLS   : **
```{x[0]}```
**◇━━━━━━━━━━◇**
**» Link GRPC  :**
```{x[2].replace(" ","")}```
**◇━━━━━━━━━━◇**
**» Format OpenClash :** 
https://{DOMAIN}:81/vless-{user}.txt
**◇━━━━━━━━━━◇**
**» Expired Until:** `{later}`
**» 🤖@WendiVpn**
"""
			await event.respond(msg,buttons=inline)
	chat = event.chat_id
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await create_vless_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)

@bot.on(events.CallbackQuery(data=b'cek-vless'))
async def cek_vless(event):
	async def cek_vless_(event):
		cmd = 'bot-cek-vless'.strip()
		x = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
		print(x)
		z = subprocess.check_output(cmd, shell=True).decode("utf-8")
		await event.respond(f"""
**◇━━━━━━━━━━◇**
	** ⟨🔸 Vless Logged🔸⟩**
**◇━━━━━━━━━━◇**
```					  
{z}
```
**Shows Logged In Users Vless**
**» 🤖@WendiVpn**
""",buttons=[[Button.inline("‹ Back ›","vless")]])
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await cek_vless_(event)
	else:
		await event.answer("Access Denied",alert=True)

@bot.on(events.CallbackQuery(data=b'delete-vless'))
async def delete_vless(event):
	async def delete_vless_(event):
		cmd = 'cat /etc/xray/config.json | grep "^#&" | cut -d " " -f 2-3 | sort | uniq | nl'.strip()
		x = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
		print(x)
		z = subprocess.check_output(cmd, shell=True).decode("utf-8")
		await event.respond(f"""
**◇━━━━━━━━━━◇**
	** ⟨🔸 Vless Account🔸⟩**
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
[Button.inline("🔄 Delet Ulang","delete-vless")],
[Button.inline("❌ Cancel","vless")]])
				return
			cmd = f'printf "%s\n" "{user}" | delvless'
		try:
			a = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
		except subprocess.CalledProcessError:  # Menangani kesalahan jika user tidak ada
			await event.respond(f" **Successfully**", buttons=[[Button.inline("‹ Back ›","vless")]])
		else:
			await event.respond(f" **Successfully Lock**", buttons=[[Button.inline("‹ Back ›","vless")]])
	chat = event.chat_id
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await delete_vless_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)

@bot.on(events.CallbackQuery(data=b'trial-vless'))
async def trial_vless(event):
	async def trial_vless_(event):
		async with bot.conversation(chat) as exp:
			await event.respond("**Choose Expiry Minutes**",buttons=[
[Button.inline(" 10 Menit ","10"),
Button.inline(" 15 Menit ","15")],
[Button.inline(" 30 Menit ","30"),
Button.inline(" 60 Menit ","60")]])
			exp = exp.wait_event(events.CallbackQuery)
			exp = (await exp).data.decode("ascii")
		cmd = f'printf "%s\n" "{exp}" | trialvless'
		try:
			a = subprocess.check_output(cmd, shell=True).decode("utf-8")
		except:
			await event.respond("**User Already Exist**")
		else:
			inline=[[Button.inline("‹ Back ›","vless")]]
			#today = DT.date.today()
			#later = today + DT.timedelta(days=int(exp))
			x = [x.group() for x in re.finditer("vless://(.*)",a)]
			print(x)
			remarks = re.search("#(.*)",x[0]).group(1)
			# domain = re.search("@(.*?):",x[0]).group(1)
			uuid = re.search("vless://(.*?)@",x[0]).group(1)
			# path = re.search("path=(.*)&",x[0]).group(1)
			msg = f"""
**◇━━━━━━━━━━◇**
		**⚡️ Xray/Vless Account ⚡️**
**◇━━━━━━━━━━◇**
**» Remarks     :** `{remarks}`
**» Host Server :** `{DOMAIN}`
**» User Quota  :** `Unlimited`
**» Port DNS    :** `443, 53`
**» port TLS    :** `222-1000`
**» Port NTLS   :** `80, 8080, 8081-9999`
**» NetWork     :** `(WS) or (gRPC)`
**» User ID     :** `{uuid}`
**» Path Vless  :** `(/multi path)/vless `
**» Path Dynamic:** `http://BUG.COM/vless `
**◇━━━━━━━━━━◇**
**» Link TLS   : **
```{x[0]}```
**◇━━━━━━━━━━◇**
**» Link GRPC  :**
```{x[2].replace(" ","")}```
**◇━━━━━━━━━━◇**
**» Format OpenClash :** 
https://{DOMAIN}:81/vless-{remarks}.txt
**◇━━━━━━━━━━◇**
**» Expired Until :** `{exp} Minutes`
**» 🤖@WendiVpn**
"""
			await event.respond(msg,buttons=inline)
	chat = event.chat_id
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await trial_vless_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)

@bot.on(events.CallbackQuery(data=b'bot-member-vl'))
async def bot_member_vl(event):
	async def bot_member_vl_(event):
		cmd = 'cat /etc/xray/config.json | grep "^#&" | cut -d " " -f 2-3 | sort | uniq | nl'.strip()
		x = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
		print(x)
		z = subprocess.check_output(cmd, shell=True).decode("utf-8")
		await event.respond(f"""
**◇━━━━━━━━━━◇**
	** ⟨🔸 Vless Account🔸⟩**
**◇━━━━━━━━━━◇**
```
{z}
```
**Menampilkan Member Vless**
**» 🤖@WendiVpn**
""",buttons=[[Button.inline("‹ Back ›","vless")]])
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await bot_member_vl_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)

@bot.on(events.CallbackQuery(data=b'renew-vl'))
async def renew_vl(event):
	async def renew_vl_(event):
		cmd = 'cat /etc/xray/config.json | grep "^#&" | cut -d " " -f 2-3 | sort | uniq | nl'.strip()
		x = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
		print(x)
		z = subprocess.check_output(cmd, shell=True).decode("utf-8")
		await event.respond(f"""
**◇━━━━━━━━━━◇**
	** ⟨🔸 Vless Account🔸⟩**
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
[Button.inline("🔄 Renew Ulang","renew-ws")],
[Button.inline("❌ Cancel","vless")]])
				return
		async with bot.conversation(chat) as exp:
			await event.respond(' **Ubah Masaaktif:**')
			exp = exp.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			exp = (await exp).raw_text
			if not exp.isdigit():
				await event.respond(" **Masaaktif harus berupa angka.**", buttons=[
[Button.inline("🔄 Renew Ulang","renew-ws")],
[Button.inline("❌ Cancel","vless")]])
				return  # Keluar dari fungsi jika exp bukan angka
		async with bot.conversation(chat) as quota:
			await event.respond(' **Limit Quota:**')
			quota = quota.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			quota = (await quota).raw_text
			if not quota.isdigit():
				await event.respond(" **Limit Quota harus berupa angka.**", buttons=[
[Button.inline("🔄 Renew Ulang","renew-ws")],
[Button.inline("❌ Cancel","vless")]])
				return  # Keluar dari fungsi jika quota bukan angka
		async with bot.conversation(chat) as ip:
			await event.respond(' **Limit Ip:**')
			ip = ip.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			ip = (await ip).raw_text
			if not ip.isdigit():
				await event.respond(" **Limit Ip harus berupa angka.**", buttons=[
[Button.inline("🔄 Renew Ulang","renew-ws")],
[Button.inline("❌ Cancel","vless")]])
				return  # Keluar dari fungsi jika ip bukan angka
			cmd = f'printf "%s\n" "{user}" "{exp}" "{quota}" "{ip}" | renewvless'
		try:
			a = subprocess.check_output(cmd, shell=True).decode("utf-8")
		except:
			await event.respond(f"**User** `{user}` **Successfully**",buttons=[[Button.inline("‹ Back ›","vless")]])
		else:
			await event.respond(f"**Successfully Renew** `{user}`",buttons=[[Button.inline("‹ Back ›","vless")]])
	chat = event.chat_id
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await renew_vl_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)


@bot.on(events.CallbackQuery(data=b'vless'))
async def vless(event):
	async def vless_(event):
		inline = [
[Button.inline("⚡️Auto Vless⚡️","auto-vless")],
[Button.inline(" ☣️Trial Vless ","trial-vless"),
Button.inline(" ➕Create Vless ","create-vless")],
[Button.inline(" 👤Member Vless ","bot-member-vl"),
Button.inline(" ♻️Renew Vless ","renew-vl")],
[Button.inline(" ✅Check Vless ","cek-vless"),
Button.inline(" ❌Delete Vless ","delete-vless")],
[Button.inline(" 🔒Lock Vless ","lock-vless"),
Button.inline(" 🔐Unlock Vless ","unlock-vless")],
[Button.inline(" 📝Detail Vless ","d-vless")],
[Button.inline("‹ Back ›","menu")]]
		z = requests.get(f"http://ip-api.com/json/?fields=country,region,city,timezone,isp").json()
		vl = f' cat /etc/vless/.vless.db | grep "###" | wc -l'
		vls = subprocess.check_output(vl, shell=True).decode("ascii")
		username = sender.username
		user_id = sender.id
		msg = f"""
**◇━━━━━━━━━━◇** 
**⚡️ VLESS MANAGER ⚡️**
**◇━━━━━━━━━━◇** 
**»🔰Service:** `VLESS`
**»🔰Jumlah VLESS  :** `{vls.strip()}` __account__
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
		await vless_(event)
	else:
		await event.answer("Access Denied",alert=True)
