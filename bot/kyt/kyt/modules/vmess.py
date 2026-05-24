from kyt import *

#detail
@bot.on(events.CallbackQuery(data=b'd-vmess'))
async def l_vmess(event):
	async def l_vmess_(event):
		cmd = 'cat /etc/xray/config.json | grep "^###" | cut -d " " -f 2-3 | sort | uniq | nl'.strip()
		x = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
		print(x)
		z = subprocess.check_output(cmd, shell=True).decode("utf-8")
		await event.respond(f"""
**◇━━━━━━━━━━◇**
	** ⟨🔸 Vmess Account🔸⟩**
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
[Button.inline("🔄 Ulangi","d-vmess")],
[Button.inline("❌ Cancel","vmess")]])
				return
			cmd = f'cat /var/www/html/vmess-{user}.txt'.strip()
			x = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
			print(x)
			z = subprocess.check_output(cmd, shell=True).decode("utf-8")
			if z:
				await event.respond(f"""
**◇━━━━━━━━━━◇**
	** ⟨🔸 Vmess Account🔸⟩**
**◇━━━━━━━━━━◇**
```
{z}
```
""",buttons=[[Button.inline("‹ Back ›","vmess")]])
			else:
				await event.respond("**Filed**: User tidak ditemukan", buttons=[[Button.inline("‹ Back ›","vmess")]])
	chat = event.chat_id
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await l_vmess_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)

#LOCK VMESS
@bot.on(events.CallbackQuery(data=b'lock-vmess'))
async def lock_vmess(event):
	async def lock_vmess_(event):
		cmd = 'cat /etc/xray/config.json | grep "^###" | cut -d " " -f 2-3 | sort | uniq | nl'.strip()
		x = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
		print(x)
		z = subprocess.check_output(cmd, shell=True).decode("utf-8")
		await event.respond(f"""
**◇━━━━━━━━━━◇**
	** ⟨🔸 Vmess Account🔸⟩**
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
[Button.inline("🔄 Lock Ulang","lock-vmess")],
[Button.inline("❌ Cancel","vmess")]])
				return
			cmd = f'printf "%s\n" "{user}" | lock-vm'
		try:
			a = subprocess.check_output(cmd, shell=True).decode("utf-8")
		except subprocess.CalledProcessError:  # Menangani kesalahan jika user tidak ada
			await event.respond(f" **Successfully**", buttons=[[Button.inline("‹ Back ›","vmess")]])
		else:
			await event.respond(f" **Successfully Lock**", buttons=[[Button.inline("‹ Back ›","vmess")]])
	chat = event.chat_id
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await lock_vmess_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)

#UNLOCK VMESS
@bot.on(events.CallbackQuery(data=b'unlock-vmess'))
async def unlock_vmess(event):
	async def unlock_vmess_(event):
		cmd = 'cat /etc/xray/.lock.db    | grep "^###" | cut -d " " -f 2-3 | sort | uniq | nl'.strip()
		x = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
		print(x)
		z = subprocess.check_output(cmd, shell=True).decode("utf-8")
		await event.respond(f"""
**◇━━━━━━━━━━◇**
	** ⟨🔸 Vmess Account🔸⟩**
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
[Button.inline("🔄 Unlock Ulang","unlock-vmess")],
[Button.inline("❌ Cancel","vmess")]])
				return  # Keluar dari fungsi jika username tidak ditemukan
			cmd = f'printf "%s\n" "{user}" | unlock-vm'
		try:
			a = subprocess.check_output(cmd, shell=True).decode("utf-8")
		except subprocess.CalledProcessError:  # Menangani kesalahan jika user tidak ada
			await event.respond(f" **Successfully**", buttons=[[Button.inline("‹ Back ›","vmess")]])
		else:
			await event.respond(f" **Successfully Unlock**", buttons=[[Button.inline("‹ Back ›","vmess")]])
	chat = event.chat_id
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await unlock_vmess_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)

#CRATE VMESS
@bot.on(events.CallbackQuery(data=b'create-vmess'))
async def create_vmess(event):
	async def create_vmess_(event):
		async with bot.conversation(chat) as user:
			await event.respond('🔡**Username:**')
			user = user.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			user = (await user).raw_text.replace(" ", "")
			cmd_check = f'cat /etc/xray/config.json | grep "{user}"'
			if subprocess.call(cmd_check, shell=True) == 0:
				await event.respond("**Username sudah ada. Silakan masukkan username baru.**", buttons=[
[Button.inline("🔄 Create Ulang","create-vmess")],
[Button.inline("❌ Cancel","vmess")]])
				return  # Keluar dari fungsi jika username sudah ada
		async with bot.conversation(chat) as limit_ip:
			await event.respond("🌐 **Limit IP:**")
			limit_ip = limit_ip.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			limit_ip = (await limit_ip).raw_text
			if not limit_ip.isdigit():
				await event.respond("🌐 **Limit IP harus berupa angka.**", buttons=[
[Button.inline("🔄 Create Ulang","create-vmess")],
[Button.inline("❌ Cancel","vmess")]])
				return  # Keluar dari fungsi jika limit_ip bukan angka
		async with bot.conversation(chat) as pw:
			await event.respond("📦 **Quota:**")
			pw = pw.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			pw = (await pw).raw_text
			if not pw.isdigit():
				await event.respond("📦 **Quota harus berupa angka.**", buttons=[
[Button.inline("🔄 Create Ulang","create-vmess")],
[Button.inline("❌ Cancel","vmess")]])
				return  # Keluar dari fungsi jika pw bukan angka
		async with bot.conversation(chat) as exp:
			await event.respond("⏳ **Masaaktif:**")
			exp = exp.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			exp = (await exp).raw_text
			if not exp.isdigit():
				await event.respond("⏳ **Masaaktif harus berupa angka.**", buttons=[
[Button.inline("🔄 Create Ulang","create-vmess")],
[Button.inline("❌ Cancel","vmess")]])
				return  # Keluar dari fungsi jika exp bukan angka
		bug = ""
		cmd = f'printf "%s\n" "{user}" "{limit_ip}" "{pw}" "{exp}" "{bug}" | addws'
		try:
			a = subprocess.check_output(cmd, shell=True).decode("utf-8")
		except:
			await event.respond(f"**User Already Exist**",buttons=[[Button.inline("‹ Back ›","menu")]])
		else:
			inline=[[Button.inline("‹ Back ›","vmess")]]
			today = DT.date.today()
			later = today + DT.timedelta(days=int(exp))
			b = [x.group() for x in re.finditer("vmess://(.*)",a)]
			print(b)
			z = base64.b64decode(b[0].replace("vmess://","")).decode("ascii")
			z = json.loads(z)
			z1 = base64.b64decode(b[1].replace("vmess://","")).decode("ascii")
			z1 = json.loads(z1)
			msg = f"""
**◇━━━━━━━━━━◇**
		**⚡️ Xray/Vmess Account ⚡️**
**◇━━━━━━━━━━◇**
**» Remarks      :** `{z["ps"]}`
**» Domain       :** `{DOMAIN}`
**» Limit IP     :** `{limit_ip}`
**» User Quota   :** `{pw} GB`
**» User ID      :** `{z["id"]}`
**» Security     :** `auto`
**» NetWork      :** `(WS) or (gRPC)`
**» Path TLS     :** `(/multi path)/vmess`
**» Path NLS     :** `(/multi path)/vmess`
**» Path Dynamic :** `http://BUG.COM`
**» ServiceName  :** `vmess-grpc`
**◇━━━━━━━━━━◇**
**» Link TLS     :** 
```{b[0].strip("'").replace(" ","")}```
**◇━━━━━━━━━━◇**
**» Link NTLS    :** 
```{b[1].strip("'").replace(" ","")}```
**◇━━━━━━━━━━◇**
**» Link GRPC    :** 
```{b[2].strip("'")}```
**◇━━━━━━━━━━◇**
**» Format OpenClash :** 
https://{DOMAIN}:81/vmess-{user}.txt
**◇━━━━━━━━━━◇**
**» Expired Until:** `{later}`
**» 🤖@WendiVpn** 
"""
			await event.respond(msg,buttons=inline)
	chat = event.chat_id
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await create_vmess_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)

# TRIAL VMESS
@bot.on(events.CallbackQuery(data=b'trial-vmess'))
async def trial_vmess(event):
	async def trial_vmess_(event):
		async with bot.conversation(chat) as exp:
			await event.respond(" **Choose Expiry Minutes**",buttons=[
[Button.inline(" 10 Menit ","10"),
Button.inline(" 15 Menit ","15")],
[Button.inline(" 30 Menit ","30"),
Button.inline(" 60 Menit ","60")]])
			exp = exp.wait_event(events.CallbackQuery)
			exp = (await exp).data.decode("ascii")
		cmd = f'printf "%s\n" "{exp}" | trialws'
		try:
			a = subprocess.check_output(cmd, shell=True).decode("utf-8")
		except:
			await event.respond("**User Already Exist**",buttons=[[Button.inline("‹ Back ›","menu")]])
		else:
			inline=[[Button.inline("‹ Back ›","vmess")]]
			today = DT.date.today()
			later = today + DT.timedelta(days=int(exp))
			b = [x.group() for x in re.finditer("vmess://(.*)",a)]
			print(b)
			z = base64.b64decode(b[0].replace("vmess://","")).decode("ascii")
			z = json.loads(z)
			z1 = base64.b64decode(b[1].replace("vmess://","")).decode("ascii")
			z1 = json.loads(z1)
			msg = f"""
**◇━━━━━━━━━━◇**
		**⚡️ Xray/Vmess Account ⚡️**
**◇━━━━━━━━━━◇**
**» Remarks      :** `{z["ps"]}`
**» Domain       :** `{DOMAIN}`
**» User Quota   :** `Unlimited`
**» User ID      :** `{z["id"]}`
**» NetWork      :** `(WS) or (gRPC)`
**» Path TLS     :** `(/multi path)/vmess`
**» Path NLS     :** `(/multi path)/vmess`
**» Path Dynamic :** `http://BUG.COM`
**» ServiceName  :** `vmess-grpc`
**◇━━━━━━━━━━◇**
**» Link TLS     :** 
```{b[0].strip("'").replace(" ","")}```
**◇━━━━━━━━━━◇**
**» Link NTLS    :** 
```{b[1].strip("'").replace(" ","")}```
**◇━━━━━━━━━━◇**
**» Link GRPC    :** 
```{b[2].strip("'")}```
**◇━━━━━━━━━━◇**
**» Format OpenClash :** 
https://{DOMAIN}:81/vmess-{z["ps"]}.txt
**◇━━━━━━━━━━◇**
**» Expired Until:** `{exp} Minutes`
**» 🤖@WendiVpn** 
"""
			await event.respond(msg,buttons=inline)
	chat = event.chat_id
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await trial_vmess_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)

# AUTO VMESS
@bot.on(events.CallbackQuery(data=b'auto-vmess'))
async def auto_vmess(event):
	async def auto_vmess_(event):
		async with bot.conversation(chat) as limit_ip:
			await event.respond("🌐 **Limit IP:**")
			limit_ip = limit_ip.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			limit_ip = (await limit_ip).raw_text
			if not limit_ip.isdigit():
				await event.respond("🌐 **Limit IP harus berupa angka.**", buttons=[
[Button.inline("🔄 Create Ulang","create-vmess")],
[Button.inline("❌ Cancel","vmess")]])
				return  # Keluar dari fungsi jika limit_ip bukan angka
		async with bot.conversation(chat) as pw:
			await event.respond("📦 **Quota:**")
			pw = pw.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			pw = (await pw).raw_text
			if not pw.isdigit():
				await event.respond("📦 **Quota harus berupa angka.**", buttons=[
[Button.inline("🔄 Create Ulang","create-vmess")],
[Button.inline("❌ Cancel","vmess")]])
				return  # Keluar dari fungsi jika pw bukan angka
		async with bot.conversation(chat) as exp:
			await event.respond("⏳ **Masaaktif:**")
			exp = exp.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			exp = (await exp).raw_text
			if not exp.isdigit():
				await event.respond("⏳ **Masaaktif harus berupa angka.**", buttons=[
[Button.inline("🔄 Create Ulang","create-vmess")],
[Button.inline("❌ Cancel","vmess")]])
				return  # Keluar dari fungsi 
		bug = ""
		user = "VmessPrem" + str(random.randint(100,1000))
		cmd_check = f'cat /etc/xray/config.json | grep "{user}"'
		if subprocess.call(cmd_check, shell=True) == 0:
			await event.respond("**Username Eror Coba Ulangi.**", buttons=[
[Button.inline("🔄 Ulangi Auto Name","auto-vmess")],
[Button.inline("❌ Cancel","vmess")]])
			return  # Keluar dari fung
		cmd = f'printf "%s\n" "{user}" "{limit_ip}" "{pw}" "{exp}" "{bug}" | addws'
		try:
			a = subprocess.check_output(cmd, shell=True).decode("utf-8")
		except:
			await event.respond("**User Already Exist**",buttons=[[Button.inline("‹ Back ›","vmess")]])
		else:
			inline=[[Button.inline("‹ Back ›","vmess")]]
			today = DT.date.today()
			later = today + DT.timedelta(days=int(exp))
			b = [x.group() for x in re.finditer("vmess://(.*)",a)]
			print(b)
			z = base64.b64decode(b[0].replace("vmess://","")).decode("ascii")
			z = json.loads(z)
			z1 = base64.b64decode(b[1].replace("vmess://","")).decode("ascii")
			z1 = json.loads(z1)
			msg = f"""
**◇━━━━━━━━━━◇**
		**⚡️ Xray/Vmess Account ⚡️**
**◇━━━━━━━━━━◇**
**» Remarks      :** `{z["ps"]}`
**» Domain       :** `{DOMAIN}`
**» Limit IP     :** `{limit_ip}`
**» User Quota   :** `Unlimited`
**» User ID      :** `{z["id"]}`
**» NetWork      :** `(WS) or (gRPC)`
**» Path TLS     :** `(/multi path)/vmess`
**» Path NLS     :** `(/multi path)/vmess`
**» Path Dynamic :** `http://BUG.COM`
**» ServiceName  :** `vmess-grpc`
**◇━━━━━━━━━━◇**
**» Link TLS     :** 
```{b[0].strip("'").replace(" ","")}```
**◇━━━━━━━━━━◇**
**» Link NTLS    :** 
```{b[1].strip("'").replace(" ","")}```
**◇━━━━━━━━━━◇**
**» Link GRPC    :** 
```{b[2].strip("'")}```
**◇━━━━━━━━━━◇**
**» Format OpenClash :** 
https://{DOMAIN}:81/vmess-{z["ps"]}.txt
**◇━━━━━━━━━━◇**
**» Expired Until:** `{later}`
**» 🤖@WendiVpn** 
"""
			await event.respond(msg,buttons=inline)
	chat = event.chat_id
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await auto_vmess_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)

@bot.on(events.CallbackQuery(data=b'bot-member-vmess'))
async def bot_member_vmess(event):
	async def bot_member_vmess_(event):
		cmd = 'cat /etc/xray/config.json | grep "^###" | cut -d " " -f 2-3 | sort | uniq | nl'.strip()
		x = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
		print(x)
		z = subprocess.check_output(cmd, shell=True).decode("utf-8")
		await event.respond(f"""
**◇━━━━━━━━━━◇**
	** ⟨🔸 Vmess Account🔸⟩**
**◇━━━━━━━━━━◇**
```
{z}
```
** Menampilkan Member Vmess**
**» 🤖@WendiVpn**
""",buttons=[[Button.inline("‹ Back ›","vmess")]])
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await bot_member_vmess_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)

#CEK VMESS
@bot.on(events.CallbackQuery(data=b'cek-vmess'))
async def cek_vmess(event):
	async def cek_vmess_(event):
		cmd = 'bot-cek-ws.sh'.strip()
		x = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
		print(x)
		z = subprocess.check_output(cmd, shell=True).decode("utf-8")
		await event.respond(f"""
**◇━━━━━━━━━━◇**
	** ⟨🔸 Vmess Logged🔸⟩**
**◇━━━━━━━━━━◇**
```					  
{z}
```
**Shows Logged In Users Vmess**
**» 🤖@WendiVpn**
""",buttons=[[Button.inline("‹ Back ›","vmess")]])
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await cek_vmess_(event)
	else:
		await event.answer("Access Denied",alert=True)
		

@bot.on(events.CallbackQuery(data=b'delete-vmess'))
async def delete_vmess(event):
	async def delete_vmess_(event):
		cmd = 'cat /etc/xray/config.json | grep "^###" | cut -d " " -f 2-3 | sort | uniq | nl'.strip()
		x = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
		print(x)
		z = subprocess.check_output(cmd, shell=True).decode("utf-8")
		await event.respond(f"""
**◇━━━━━━━━━━◇**
	** ⟨🔸 Vmess Account🔸⟩**
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
[Button.inline("🔄 Delet Ulang","delete-vmess")],
[Button.inline("❌ Cancel","vmess")]])
				return
			cmd = f'printf "%s\n" "{user}" | delws'
		try:
			a = subprocess.check_output(cmd, shell=True).decode("utf-8")
		except subprocess.CalledProcessError:  # Menangani kesalahan jika user tidak ada
			await event.respond(f" **Successfully**", buttons=[[Button.inline("‹ Back ›","vmess")]])
		else:
			await event.respond(f" **Successfully Delet**", buttons=[[Button.inline("‹ Back ›","vmess")]])
	chat = event.chat_id
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await delete_vmess_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)

@bot.on(events.CallbackQuery(data=b'renew-ws'))
async def renew_ws(event):
	async def renew_ws_(event):
		cmd = 'cat /etc/xray/config.json | grep "^###" | cut -d " " -f 2-3 | sort | uniq | nl'.strip()
		x = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
		print(x)
		z = subprocess.check_output(cmd, shell=True).decode("utf-8")
		await event.respond(f"""
**◇━━━━━━━━━━◇**
	** ⟨🔸 Vmess Account🔸⟩**
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
[Button.inline("❌ Cancel","vmess")]])
				return
		async with bot.conversation(chat) as exp:
			await event.respond(' **Ubah Masaaktif:**')
			exp = exp.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			exp = (await exp).raw_text
			if not exp.isdigit():
				await event.respond(" **Masaaktif harus berupa angka.**", buttons=[
[Button.inline("🔄 Renew Ulang","renew-ws")],
[Button.inline("❌ Cancel","vmess")]])
				return  # Keluar dari fungsi jika exp bukan angka
		async with bot.conversation(chat) as quota:
			await event.respond(' **Limit Quota:**')
			quota = quota.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			quota = (await quota).raw_text
			if not quota.isdigit():
				await event.respond(" **Limit Quota harus berupa angka.**", buttons=[
[Button.inline("🔄 Renew Ulang","renew-ws")],
[Button.inline("❌ Cancel","vmess")]])
				return  # Keluar dari fungsi jika quota bukan angka
		async with bot.conversation(chat) as ip:
			await event.respond(' **Limit Ip:**')
			ip = ip.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			ip = (await ip).raw_text
			if not ip.isdigit():
				await event.respond(" **Limit Ip harus berupa angka.**", buttons=[
[Button.inline("🔄 Renew Ulang","renew-ws")],
[Button.inline("❌ Cancel","vmess")]])
				return  # Keluar dari fungsi jika ip bukan angka
			cmd = f'printf "%s\n" "{user}" "{exp}" "{quota}" "{ip}" | renewws'
		try:
			a = subprocess.check_output(cmd, shell=True).decode("utf-8")
		except:
			await event.respond(f"**User** `{user}` **Successfully**",buttons=[[Button.inline("‹ Back ›","vmess")]])
		else:
			await event.respond(f"**Successfully Renew** `{user}`",buttons=[[Button.inline("‹ Back ›","vmess")]])
	chat = event.chat_id
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await renew_ws_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)

@bot.on(events.CallbackQuery(data=b'vmess'))
async def vmess(event):
	async def vmess_(event):
		inline = [
[Button.inline("⚡️Auto Vmess⚡️","auto-vmess")],
[Button.inline("☣️Trial Vmess","trial-vmess"),
Button.inline("➕Create Vmess","create-vmess")],
[Button.inline("♻️Renew Vmess","renew-ws"),
Button.inline("👤Member Vmess","bot-member-vmess")],
[Button.inline("✅Check Vmess","cek-vmess"),
Button.inline("❌Delete Vmess","delete-vmess")],
[Button.inline("🔒Lock Vmess","lock-vmess"),
Button.inline("🔐Unlock Vmess","unlock-vmess")],
[Button.inline("📝Detail Vmess","d-vmess")],
[Button.inline("‹ Back ›","menu")]]
		z = requests.get(f"http://ip-api.com/json/?fields=country,region,city,timezone,isp").json()
		vm = f' cat /etc/xray/config.json | grep "###" | wc -l'
		vms = subprocess.check_output(vm, shell=True).decode("ascii")
		user_id = sender.id
		username = sender.username
		msg = f"""
**◇━━━━━━━━━━◇**
**⚡️ VMESS MANAGER ⚡️**
**◇━━━━━━━━━━◇** 
**»🔰Service:** `VMESS`
**»🔰Jumlah VMESS  :** `{vms.strip()}` __account__
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
		await vmess_(event)
	else:
		await event.answer("Access Denied",alert=True)