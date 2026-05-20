from kyt import *

#detail
@bot.on(events.CallbackQuery(data=b'd-ssh'))
async def l_ssh(event):
	async def l_ssh_(event):
		cmd = 'bot-member-ssh'.strip()
		x = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
		print(x)
		z = subprocess.check_output(cmd, shell=True).decode("utf-8")
		await event.respond(f"""
**◇━━━━━━━━━━◇**
	** ⟨🔸 SSH Account🔸⟩**
**◇━━━━━━━━━━◇**
```
{z}
```
""")
		async with bot.conversation(chat) as user:
			await event.respond(" **🔡Username:**")
			user_event = user.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			user = (await user_event).raw_text.replace(" ", "")
			cmd_check = f'grep -E "^{user}:" /etc/passwd'
			if subprocess.call(cmd_check, shell=True) != 0:
				await event.respond("**Username tidak ditemukan. Silakan masukkan username yang benar.**", buttons=[
[Button.inline("🔄 Ulangi","d-ssh")],
[Button.inline("‹ Back ›","ssh")]])
				return
			cmd = f'cat /var/www/html/ssh-{user}.txt'.strip()
			x = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
			print(x)
			z = subprocess.check_output(cmd, shell=True).decode("utf-8")
			if z:
				await event.respond(f"""
**◇━━━━━━━━━━◇**
	** ⟨🔸 SSH Account🔸⟩**
**◇━━━━━━━━━━◇**
```
{z}
```
""",buttons=[[Button.inline("‹ Back ›","ssh")]])
			else:
				await event.respond("**Filed**: User tidak ditemukan", buttons=[[Button.inline("‹ Back ›","ssh")]])
	chat = event.chat_id
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await l_ssh_(event)
	else:
		await event.answer("Akses Ditolak",alert=True) 

#UNLOCKSSH
@bot.on(events.CallbackQuery(data=b'user-unlock'))
async def user_unlock(event):
	async def user_unlock_(event):
		cmd = 'bot-member-ssh'.strip()
		x = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
		print(x)
		z = subprocess.check_output(cmd, shell=True).decode("utf-8")
		await event.respond(f"""
**◇━━━━━━━━━━◇**
	** ⟨🔸 SSH Account🔸⟩**
**◇━━━━━━━━━━◇**
```
{z}
```
""")

		async with bot.conversation(chat) as user:
			await event.respond(" **🔡Username:**")
			user_event = user.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			user = (await user_event).raw_text.replace(" ", "")
			cmd_check = f'grep -E "^{user}:" /etc/passwd'
			if subprocess.call(cmd_check, shell=True) != 0:
				await event.respond("**Username tidak ditemukan. Silakan masukkan username yang benar.**", buttons=[
[Button.inline("🔄 Unlock Ulang","user-unlock")],
[Button.inline("‹ Back ›","ssh")]])
				return  # Keluar dari fun
			cmd = f'printf "%s\n" "{user}" | user-unlock.sh'
		try:
			a = subprocess.check_output(cmd, shell=True).decode("utf-8")
		except subprocess.CalledProcessError:  # Menangani kesalahan jika user tidak ada
			await event.respond(f" **Successfully**", buttons=[[Button.inline("‹ Back ›","ssh")]])
		else:
			await event.respond(f" **Successfully Unlock**", buttons=[[Button.inline("‹ Back ›","ssh")]])
	chat = event.chat_id
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await user_unlock_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)

#LOCKSSH
@bot.on(events.CallbackQuery(data=b'user-lock'))
async def user_lock(event):
	async def user_lock_(event):
		cmd = 'bot-member-ssh'.strip()
		x = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
		print(x)
		z = subprocess.check_output(cmd, shell=True).decode("utf-8")
		await event.respond(f"""
**◇━━━━━━━━━━◇**
	** ⟨🔸 SSH Account🔸⟩**
**◇━━━━━━━━━━◇**
```
{z}
```
""")
		async with bot.conversation(chat) as user:
			await event.respond(" **🔡Username:**")
			user_event = user.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			user = (await user_event).raw_text.replace(" ", "")
			cmd_check = f'grep -E "^{user}:" /etc/passwd'
			if subprocess.call(cmd_check, shell=True) != 0:
				await event.respond("**Username tidak ditemukan. Silakan masukkan username yang benar.**", buttons=[
[Button.inline("🔄 Lock Ulang","user-lock")],
[Button.inline("‹ Back ›","ssh")]])
				return
			cmd = f'printf "%s\n" "{user}" | user-lock.sh'
		try:
			a = subprocess.check_output(cmd, shell=True).decode("utf-8")
		except subprocess.CalledProcessError:  # Menangani kesalahan jika user tidak ada
			await event.respond(f" **Successfully**", buttons=[[Button.inline("‹ Back ›","ssh")]])
		else:
			await event.respond(f" **Successfully Lock**", buttons=[[Button.inline("‹ Back ›","ssh")]])
	chat = event.chat_id
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await user_lock_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)

#DELETESSH
@bot.on(events.CallbackQuery(data=b'delete-ssh'))
async def delete_ssh(event):
	async def delete_ssh_(event):
		cmd = 'bot-member-ssh'.strip()
		x = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
		print(x)
		z = subprocess.check_output(cmd, shell=True).decode("utf-8")
		await event.respond(f"""
**◇━━━━━━━━━━◇**
	** ⟨🔸 SSH Account🔸⟩**
**◇━━━━━━━━━━◇**
```
{z}
```
""")
		async with bot.conversation(chat) as user:
			await event.respond(' **🔡Username:**')
			user_event = user.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			user = (await user_event).raw_text.replace(" ", "")
			cmd_check = f'grep -E "^{user}:" /etc/passwd'
			if subprocess.call(cmd_check, shell=True) != 0:
				await event.respond("**Username tidak ditemukan. Silakan masukkan username yang benar.**", buttons=[
[Button.inline("🔄 Delet Ulang","delete-ssh")],
[Button.inline("‹ Back ›","ssh")]])
				return
			cmd = f'printf "%s\n" "{user}" | delssh'
		try:
			a = subprocess.check_output(cmd, shell=True).decode("utf-8")
		except subprocess.CalledProcessError:  # Menangani kesalahan jika user tidak ada
			await event.respond(f" **Successfully**", buttons=[[Button.inline("‹ Back ›","ssh")]])
		else:
			await event.respond(f" **Successfully Delet**", buttons=[[Button.inline("‹ Back ›","ssh")]])
	chat = event.chat_id
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await delete_ssh_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)

@bot.on(events.CallbackQuery(data=b'create-ssh'))
async def create_ssh(event):
	async def create_ssh_(event):
		async with bot.conversation(chat) as user:
			await event.respond('🔡**Username:**')
			user_event = user.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			user = (await user_event).raw_text.replace(" ", "")
			cmd_check = f'grep -E "^{user}:" /etc/passwd'
			if subprocess.call(cmd_check, shell=True) == 0:
				await event.respond("**Username sudah ada. Silakan masukkan username baru.**", buttons=[
[Button.inline("🔄 Create Ulang","create-ssh")],
[Button.inline("‹ Back ›","ssh")]])
				return  # Keluar dari fungsi jika username sudah ada
		async with bot.conversation(chat) as pw:
			await event.respond("📦 **Passwd:**")
			pw = pw.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			pw = (await pw).raw_text.replace(" ", "")
		async with bot.conversation(chat) as limit_ip:
			await event.respond("🌐 **Limit IP:**")
			limit_ip = limit_ip.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			limit_ip = (await limit_ip).raw_text
			if not limit_ip.isdigit():
				await event.respond("🌐 **Limit IP harus berupa angka.**", buttons=[
[Button.inline("🔄 Create Ulang","create-ssh")],
[Button.inline("❌ Cancel","ssh")]])
				return  # Keluar dari fungsi jika limit_ip bukan angka
		async with bot.conversation(chat) as exp:
			await event.respond("⏳ **Masaaktif:**")
			exp = exp.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			exp = (await exp).raw_text
			if not exp.isdigit():
				await event.respond("⏳ **Masaaktif harus berupa angka.**", buttons=[
[Button.inline("🔄 Create Ulang","create-ssh")],
[Button.inline("❌ Cancel","ssh")]])
				return  # Keluar dari fungsi jika exp bukan angka
		bug = ""
		cmd = f'printf "%s\n" "{user}" "{pw}" "{limit_ip}" "{exp}" "{bug}" | addssh'
		try:
			subprocess.check_output(cmd,shell=True)
		except:
			await event.respond("**User Already Exist**",buttons=[[Button.inline("‹ Back ›","ssh")]])
		else:
			inline=[[Button.inline("‹ Main Menu ›","menu")]]
			today = DT.date.today()
			later = today + DT.timedelta(days=int(exp))
			msg = f"""
**◇━━━━━━━━━━◇**
		**⚡️  SSH OVPN ACCOUNT ⚡️**
**◇━━━━━━━━━━◇**
**» Username         :** `{user.strip()}`
**» Password         :** `{pw.strip()}`
**◇━━━━━━━━━━◇**
**» Host             :** `{DOMAIN}`
**» Limit IP         :** `{limit_ip.strip()}`
**» Port OpenSSH     :** `443, 80, 22`
**◇━━━━━━━━━━◇**
**» OpenSSH:** 
`{DOMAIN}:80@{user.strip()}:{pw.strip()}`
**◇━━━━━━━━━━◇**
**» SSH WS:** 
`{DOMAIN}:443@{user.strip()}:{pw.strip()}`
**◇━━━━━━━━━━◇**
**» UDP:** 
`{DOMAIN}:1-65535@{user.strip()}:{pw.strip()}`
**◇━━━━━━━━━━◇**
**» Payload WSS      :** 
```GET wss://{bug.strip()}/ HTTP/1.1[crlf]Host: {DOMAIN}[crlf]Upgrade: websocket[crlf][crlf]```
**◇━━━━━━━━━━◇**
**» OpenVPN WS SSL   :** `https://{DOMAIN}:81/ws-ssl.ovpn`
**» OpenVPN SSL      :** `https://{DOMAIN}:81/ssl.ovpn`
**» OpenVPN TCP      :** `https://{DOMAIN}:81/tcp.ovpn`
**» OpenVPN UDP      :** `https://{DOMAIN}:81/udp.ovpn`
**◇━━━━━━━━━━◇**
**» Save Link Account:** https://{DOMAIN}:81/ssh-{user.strip()}.txt
**» Expired Until:** `{later}`
**» 🤖@WendiVpn**
"""
			await event.respond(msg,buttons=inline)
	chat = event.chat_id
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await create_ssh_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)

@bot.on(events.CallbackQuery(data=b'show-ssh'))
async def show_ssh(event):
	async def show_ssh_(event):
		cmd = 'bot-member-ssh'.strip()
		x = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
		print(x)
		z = subprocess.check_output(cmd, shell=True).decode("utf-8")
		await event.respond(f"""
**◇━━━━━━━━━━◇**
	** ⟨🔸 SSH Account🔸⟩**
**◇━━━━━━━━━━◇**
```
{z}
```
**Show All SSH User**
**» 🤖@WendiVpn**
""",buttons=[[Button.inline("‹ Back ›","ssh")]])
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await show_ssh_(event)
	else:
		await event.answer("Access Denied",alert=True)


@bot.on(events.CallbackQuery(data=b'auto-ssh'))
async def auto_ssh(event):
	async def auto_ssh_(event):
		async with bot.conversation(chat) as pw:
			await event.respond("📦 **Passwd:**")
			pw = pw.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			pw = (await pw).raw_text.replace(" ", "")
		async with bot.conversation(chat) as limit_ip:
			await event.respond("🌐 **Limit IP:**")
			limit_ip = limit_ip.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			limit_ip = (await limit_ip).raw_text
			if not limit_ip.isdigit():
				await event.respond("🌐 **Limit IP harus berupa angka.**", buttons=[
[Button.inline("🔄 Create Ulang","auto-ssh")],
[Button.inline("❌ Cancel","ssh")]])
				return  # Keluar dari fungsi jika limit_ip bukan angka
		async with bot.conversation(chat) as exp:
			await event.respond("⏳ **Masaaktif:**")
			exp = exp.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			exp = (await exp).raw_text
			if not exp.isdigit():
				await event.respond("⏳ **Masaaktif harus berupa angka.**", buttons=[
[Button.inline("🔄 Auto Ulang","auto-ssh")],
[Button.inline("❌ Cancel","ssh")]])
				return  # Keluar dari fungsi jika exp bukan angka
		bug = ""
		user = "Premium"+str(random.randint(100,1000))
		cmd_check = f'cat /etc/shadow | grep "{user}"'
		if subprocess.call(cmd_check, shell=True) == 0:
			await event.respond("**Username Eror Coba Ulangi.**", buttons=[
[Button.inline("🔄 Ulangi Auto Name","auto-ssh")],
[Button.inline("❌ Cancel","ssh")]])
			return  # Keluar dari fung
		cmd = f'printf "%s\n" "{user}" "{pw}" "{limit_ip}" "{exp}" "{bug}" | addssh'
		try:
			subprocess.check_output(cmd,shell=True)
		except:
			await event.respond("**User Already Exist**",buttons=[[Button.inline("‹ Menu Utama ›","menu")]])
		else:
			inline=[[Button.inline("‹ Back ›","ssh")]]
			today = DT.date.today()
			later = today + DT.timedelta(days=int(exp))
			msg = f""" 
**◇━━━━━━━━━━◇**
		**⚡️ SSH OVPN ACCOUNT AUTO ⚡️**
**◇━━━━━━━━━━◇**
**» Username         :** `{user.strip()}`
**» Password         :** `{pw.strip()}`
**◇━━━━━━━━━━◇**
**» Host             :** `{DOMAIN}`
**» Limit IP         :** `{limit_ip.strip()}`
**◇━━━━━━━━━━◇**
**» OpenSSH:** 
`{DOMAIN}:80@{user.strip()}:{pw.strip()}`
**◇━━━━━━━━━━◇**
**» SSH WS:** 
`{DOMAIN}:443@{user.strip()}:{pw.strip()}`
**◇━━━━━━━━━━◇**
**» UDP:** 
`{DOMAIN}:1-65535@{user.strip()}:{pw.strip()}`
**◇━━━━━━━━━━◇**
**» Payload WSS      :** 
```GET wss://{bug.strip()}/ HTTP/1.1[crlf]Host: {DOMAIN}[crlf]Upgrade: websocket[crlf][crlf]```
**◇━━━━━━━━━━◇**
**» OpenVPN WS SSL   :** `https://{DOMAIN}:81/ws-ssl.ovpn`
**» OpenVPN SSL      :** `https://{DOMAIN}:81/ssl.ovpn`
**» OpenVPN TCP      :** `https://{DOMAIN}:81/tcp.ovpn`
**» OpenVPN UDP      :** `https://{DOMAIN}:81/udp.ovpn`
**◇━━━━━━━━━━◇**
**» Save Link Account:** https://{DOMAIN}:81/ssh-{user.strip()}.txt
**» Expired Until:** `{later}`
**» 🤖@WendiVpn**
"""
			await event.respond(msg,buttons=inline)
	chat = event.chat_id
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await auto_ssh_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)

@bot.on(events.CallbackQuery(data=b'trial-ssh'))
async def trial_ssh(event):
	async def trial_ssh_(event):
		async with bot.conversation(chat) as exp:
			await event.respond("**⏳Choose Expiry Minutes⏳**",buttons=[
[Button.inline(" ⏳10 Menit⏳ ","10"),
Button.inline(" ⏳15 Menit⏳ ","15")],
[Button.inline(" ⏳30 Menit⏳ ","30"),
Button.inline(" ⏳60 Menit⏳ ","60")]])
			exp = exp.wait_event(events.CallbackQuery)
			exp = (await exp).data.decode("ascii")
		user = "trialX"+str(random.randint(100,1000))
		pw = "1"
		limit_ip = "4"
		cmd = f'printf "%s\n" "{user}" "{pw}" "{limit_ip}" "{exp}" | trial'
		try:
			subprocess.check_output(cmd,shell=True)
		except:
			await event.respond("**User Already Exist**",buttons=[[Button.inline("‹ Back ›","ssh")]])
		else:
			inline=[[Button.inline("‹ Back ›","ssh")]]
			today = DT.date.today()
			later = today + DT.timedelta(days=int(exp))
			msg = f"""
**◇━━━━━━━━━━◇**
		**⚡️ SSH OVPN ACCOUNT ⚡️**
**◇━━━━━━━━━━◇**
**» Username         :** `{user.strip()}`
**» Password         :** `{pw.strip()}`
**◇━━━━━━━━━━◇**
**» Host             :** `{DOMAIN}`
**» Limit IP         :** `{limit_ip.strip()}`
**◇━━━━━━━━━━◇**
**» OpenSSH:** 
`{DOMAIN}:80@{user.strip()}:{pw.strip()}`
**◇━━━━━━━━━━◇**
**» SSH WS:** 
`{DOMAIN}:443@{user.strip()}:{pw.strip()}`
**◇━━━━━━━━━━◇**
**» UDP:** 
`{DOMAIN}:1-65535@{user.strip()}:{pw.strip()}`
**◇━━━━━━━━━━◇**
**» Payload WSS      :** 
```GET wss://BUG.COM/ HTTP/1.1[crlf]Host: {DOMAIN}[crlf]Upgrade: websocket[crlf][crlf]```
**◇━━━━━━━━━━◇**
**» OpenVPN WS SSL   :** `https://{DOMAIN}:81/ws-ssl.ovpn`
**» OpenVPN SSL      :** `https://{DOMAIN}:81/ssl.ovpn`
**» OpenVPN TCP      :** `https://{DOMAIN}:81/tcp.ovpn`
**» OpenVPN UDP      :** `https://{DOMAIN}:81/udp.ovpn`
**◇━━━━━━━━━━◇**
**» Save Link Account:** https://{DOMAIN}:81/ssh-{user.strip()}.txt
**» Expired Until:** `{exp} Minutes`
**» 🤖@WendiVpn**
"""
			await event.respond(msg,buttons=inline)
	chat = event.chat_id
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await trial_ssh_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)
		
		
@bot.on(events.CallbackQuery(data=b'login-ssh'))
async def login_ssh(event):
	async def login_ssh_(event):
		# Gunakan subprocess.run agar tidak throw exception saat script exit non-zero
		try:
			result = subprocess.run(
				'bot-cek-login-ssh', shell=True,
				stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
				timeout=30
			)
			z = result.stdout.decode("utf-8", errors="replace").strip()
		except subprocess.TimeoutExpired:
			z = "⚠️ Timeout: script terlalu lama dijalankan"
		except Exception as e:
			z = f"⚠️ Error: {str(e)}"

		if not z:
			z = "Tidak ada user yang aktif saat ini"

		header = "**◇━━━━━━━━━━◇**\n\t**⟨🔸 SSH Login🔸⟩**\n**◇━━━━━━━━━━◇**\n"
		footer = "\n**» 🤖@WendiVpn**"
		back_btn = [[Button.inline("‹ Back ›","ssh")]]
		MAX_LEN = 3500  # Telegram limit 4096, sisakan ruang untuk header/footer

		if len(z) > MAX_LEN:
			# Split output menjadi beberapa pesan
			chunks = [z[i:i+MAX_LEN] for i in range(0, len(z), MAX_LEN)]
			for i, chunk in enumerate(chunks):
				if i == 0:
					await event.respond(
						f"{header}```\n{chunk}\n```{footer}",
						buttons=back_btn
					)
				else:
					await event.respond(f"```\n{chunk}\n```")
		else:
			await event.respond(
				f"{header}```\n{z}\n```{footer}",
				buttons=back_btn
			)
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await login_ssh_(event)
	else:
		await event.answer("Access Denied",alert=True)
		
@bot.on(events.CallbackQuery(data=b'renew-ssh'))
async def renew_ssh(event):
	async def renew_ssh_(event):
		cmd = 'bot-member-ssh'.strip()
		x = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
		print(x)
		z = subprocess.check_output(cmd, shell=True).decode("utf-8")
		await event.respond(f"""
**◇━━━━━━━━━━◇**
	** ⟨🔸 SSH Account🔸⟩**
**◇━━━━━━━━━━◇**
```
{z}
```
""")
		async with bot.conversation(chat) as conv_user:
			await event.respond(' **🔡Username Renew:**')
			user_event = conv_user.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			user = (await user_event).raw_text.replace(" ", "")
			cmd_check = f'grep -E "^{user}:" /etc/passwd'
			if subprocess.call(cmd_check, shell=True) != 0:
				await event.respond("**Username tidak ditemukan. Silakan masukkan username yang benar.**", buttons=[
[Button.inline("🔄 Renew Ulang","renew-ssh")],
[Button.inline("‹ Back ›","ssh")]])
				return
		async with bot.conversation(chat) as conv_exp:
			await event.respond(' **Ubah Masaaktif:**')
			exp_event = conv_exp.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			exp = (await exp_event).raw_text
			if not exp.isdigit():
				await event.respond(" **Masaaktif harus berupa angka.**", buttons=[
[Button.inline("🔄 Renew Ulang","renew-ssh")],
[Button.inline("‹ Back ›","ssh")]])
				return  # Keluar dari fungsi jika exp bukan angka
		cmd = f'printf "%s\n" "{user}" "{exp}" | renewssh'
		try:
			a = subprocess.check_output(cmd, shell=True).decode("utf-8")
		except:
			await event.respond(f"**User** `{user}` **Successfully**",buttons=[[Button.inline("‹ Back ›","ssh")]])
		else:
			await event.respond(f"**Successfully Renew** `{user}`",buttons=[[Button.inline("‹ Back ›","ssh")]])
	chat = event.chat_id
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await renew_ssh_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)

@bot.on(events.CallbackQuery(data=b'ssh'))
async def ssh(event):
	async def ssh_(event):
		inline = [
[Button.inline(" ⚡️Auto SSH⚡️ ","auto-ssh")],
[Button.inline(" ☣️Trial SSH ","trial-ssh"),
Button.inline(" ➕Create SSH ","create-ssh")],
[Button.inline(" ❌Delete SSH ","delete-ssh"),
Button.inline(" ✅Check SSH ","login-ssh")],
[Button.inline(" 👤User SSH ","show-ssh"),
Button.inline(" ♻️Renew SSH ","renew-ssh")],
[Button.inline(" 🔒Lock SSH ","user-lock"),
Button.inline(" 🔐Unlock SSH ","user-unlock")],
[Button.inline(" 📝Detail SSH ","d-ssh")],
[Button.inline("‹ Back ›","menu")]]
		z = requests.get(f"http://ip-api.com/json/?fields=country,region,city,timezone,isp").json()
		sh = f'cat /etc/ssh/.ssh.db | grep "###" | wc -l'
		ssh_count = subprocess.check_output(sh, shell=True).decode("ascii").strip()
		username = sender.username
		user_id = sender.id
		msg = f"""
**◇━━━━━━━━━━◇**
**⚡️ SSH OVPN MANAGER ⚡️**
**◇━━━━━━━━━━◇**
**»🔰Service:** `SSH OVPN`
**»🔰Jumlah SSH OVPN :** `{ssh_count}` __akun__
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
		await ssh_(event)
	else:
		await event.answer("Access Denied",alert=True)
