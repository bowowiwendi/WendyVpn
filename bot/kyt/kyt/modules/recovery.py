from kyt import *
from datetime import datetime, timedelta

@bot.on(events.CallbackQuery(data=b'rercvm'))
async def rerc_ws(event):
	async def rerc_ws_(event):
		cmd = 'cat /etc/xray/.lock.db | grep "^###" | cut -d " " -f 2-3 | sort | uniq | nl'.strip()
		x = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
		print(x)
		z = subprocess.check_output(cmd, shell=True).decode("utf-8")
		await event.respond(f"""
**◇━━━━━━━━━━━━━━━━━━◇**
	** ⟨🔸 Renew Recovery🔸⟩**
**◇━━━━━━━━━━━━━━━━━━◇**
```
{z}
```
""")
		async with bot.conversation(chat) as user:
			await event.respond('**Username Renew:**')
			user = user.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			user = (await user).raw_text.replace(" ", "")
		async with bot.conversation(chat) as exp:
			await event.respond('**Ubah Masaaktif:**')
			exp = exp.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			exp = (await exp).raw_text.replace(" ", "")
		get_uuid = f"cat /etc/xray/.lock.db | grep -w '^### {user}' | cut -d ' ' -f 4"
		try:
			uuid = subprocess.check_output(get_uuid, shell=True).decode().strip()
		except:
			await event.respond(f"**User** `{user}` **Not Found**",buttons=[[Button.inline("‹ Back ›","recovery")]])
			return
		cmd = 'renew-lock'
		try:
			subprocess.check_output(cmd, shell=True)
			await event.respond(f"**Successfully Renew** `{user}`",buttons=[[Button.inline("‹ Back ›","recovery")]])
		except:
			await event.respond(f"**Failed to renew user** `{user}`",buttons=[[Button.inline("‹ Back ›","recovery")]])
	chat = event.chat_id
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await rerc_ws_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)
		
@bot.on(events.CallbackQuery(data=b'rercvl'))
async def rerc_vl(event):
	async def rerc_vl_(event):
		cmd = 'cat /etc/xray/.lock.db | grep "^#&" | cut -d " " -f 2-3 | sort | uniq | nl'.strip()
		x = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
		print(x)
		z = subprocess.check_output(cmd, shell=True).decode("utf-8")
		await event.respond(f"""
**◇━━━━━━━━━━━━━━━━━━◇**
	** ⟨🔸 Renew Recovery🔸⟩**
**◇━━━━━━━━━━━━━━━━━━◇**
```
{z}
```
""")
		async with bot.conversation(chat) as user:
			await event.respond('**Username Renew:**')
			user = user.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			user = (await user).raw_text.replace(" ", "")
		async with bot.conversation(chat) as exp:
			await event.respond('**Ubah Masaaktif:**')
			exp = exp.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			exp = (await exp).raw_text.replace(" ", "")
		get_uuid = f"cat /etc/xray/.lock.db | grep -w '^#& {user}' | cut -d ' ' -f 4"
		try:
			uuid = subprocess.check_output(get_uuid, shell=True).decode().strip()
		except:
			await event.respond(f"**User** `{user}` **Not Found**",buttons=[[Button.inline("‹ Back ›","recovery")]])
			return
		cmd = f'renew-lock'
		try:
			subprocess.check_output(cmd, shell=True)
			await event.respond(f"**Successfully Renew** `{user}`",buttons=[[Button.inline("‹ Back ›","recovery")]])
		except:
			await event.respond(f"**Failed to renew user** `{user}`",buttons=[[Button.inline("‹ Back ›","recovery")]])
	chat = event.chat_id
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await rerc_vl_(event)
	else:
			await event.answer("Akses Ditolak",alert=True)
		
@bot.on(events.CallbackQuery(data=b'rerctr'))
async def rerc_tr(event):
	async def rerc_tr_(event):
		cmd = 'cat /etc/xray/.lock.db | grep "^#!" | cut -d " " -f 2-3 | sort | uniq | nl'.strip()
		x = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
		print(x)
		z = subprocess.check_output(cmd, shell=True).decode("utf-8")
		await event.respond(f"""
**◇━━━━━━━━━━━━━━━━━━◇**
	** ⟨🔸 Renew Recovery🔸⟩**
**◇━━━━━━━━━━━━━━━━━━◇**
```
{z}
```
""")
		async with bot.conversation(chat) as user:
			await event.respond('**Username Renew:**')
			user = user.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			user = (await user).raw_text.replace(" ", "")
		async with bot.conversation(chat) as exp:
			await event.respond('**Ubah Masaaktif:**')
			exp = exp.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			exp = (await exp).raw_text.replace(" ", "")
		get_uuid = f"cat /etc/xray/.lock.db | grep -w '^#! {user}' | cut -d ' ' -f 4"
		try:
			uuid = subprocess.check_output(get_uuid, shell=True).decode().strip()
		except:
			await event.respond(f"**User** `{user}` **Not Found**",buttons=[[Button.inline("‹ Back ›","recovery")]])
			return
		# Menghitung dan memformat tanggal kadaluarsa
		current_date = datetime.now()
		new_exp_date = current_date + timedelta(days=int(exp))
		exp2 = new_exp_date.strftime("%Y%m%d")
		# Memperbaiki command untuk menghapus \n yang tidak perlu dan memperbaiki format
		cmd = 'renew-lock'
		try:
			subprocess.check_output(cmd, shell=True)
			await event.respond(f"**Successfully Renew** `{user}`",buttons=[[Button.inline("‹ Back ›","recovery")]])
		except:
			await event.respond(f"**Failed to renew user** `{user}`",buttons=[[Button.inline("‹ Back ›","recovery")]])
	chat = event.chat_id
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await rerc_tr_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)

@bot.on(events.CallbackQuery(data=b'delrcvm'))
async def del_vmess(event):
	async def del_vmess_(event):
		cmd = 'cat /etc/xray/.lock.db | grep "^###" | cut -d " " -f 2-3 | sort | uniq | nl'
		z = subprocess.check_output(cmd, shell=True).decode("utf-8")
		await event.respond(f"""
**◇━━━━━━━━━━━━━━━━━━◇**
	** ⟨🔸 Delet Recovery🔸⟩**
**◇━━━━━━━━━━━━━━━━━━◇**
```
{z}
```
""")
		async with bot.conversation(chat) as user:
			await event.respond('**Username:**')
			user = user.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			user = (await user).raw_text.replace(" ", "")
		cmd = f'sed -i "/^### {user}/d" /etc/xray/.lock.db'
		try:
			subprocess.check_output(cmd, shell=True)
			await event.respond(f"**Successfully Deleted** `{user}`",
								buttons=[[Button.inline("‹ Back ›","recovery")]])
		except:
			await event.respond(f"**Failed to delete user** `{user}`",
								buttons=[[Button.inline("‹ Back ›","recovery")]])
	chat = event.chat_id
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await del_vmess_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)
		
@bot.on(events.CallbackQuery(data=b'delrcvl'))
async def del_vless(event):
	async def del_vless_(event):
		cmd = 'cat /etc/xray/.lock.db | grep "^#&" | cut -d " " -f 2-3 | sort | uniq | nl'.strip()
		x = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
		print(x)
		z = subprocess.check_output(cmd, shell=True).decode("utf-8")
		await event.respond(f"""
**◇━━━━━━━━━━━━━━━━━━◇**
	** ⟨🔸 Delet Recovery🔸⟩**
**◇━━━━━━━━━━━━━━━━━━◇**
```
{z}
```
""")
		async with bot.conversation(chat) as user:
			await event.respond('**Username:**')
			user = user.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			user = (await user).raw_text.replace(" ", "")
		cmd = f'sed -i "/^#& {user}/d" /etc/xray/.lock.db'
		try:
			subprocess.check_output(cmd, shell=True)
			await event.respond(f"**Successfully Deleted** `{user}`",
								buttons=[[Button.inline("‹ Back ›","recovery")]])
		except:
			await event.respond(f"**Failed to delete user** `{user}`",
								buttons=[[Button.inline("‹ Back ›","recovery")]])
	chat = event.chat_id
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await del_vless_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)

@bot.on(events.CallbackQuery(data=b'delrctr'))
async def del_trojan(event):
	async def del_trojan_(event):
		cmd = 'cat /etc/xray/.lock.db | grep "^#!" | cut -d " " -f 2-3 | sort | uniq | nl'.strip()
		x = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
		print(x)
		z = subprocess.check_output(cmd, shell=True).decode("utf-8")
		await event.respond(f"""
**◇━━━━━━━━━━━━━━━━━━◇**
	** ⟨🔸 Delet Recovery🔸⟩**
**◇━━━━━━━━━━━━━━━━━━◇**
```
{z}
```
""")
		async with bot.conversation(chat) as user:
			await event.respond('**Username:**')
			user = user.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			user = (await user).raw_text.replace(" ", "")
		cmd = f'sed -i "/^#! {user}/d" /etc/xray/.lock.db'
		try:
			subprocess.check_output(cmd, shell=True)
			await event.respond(f"**Successfully Deleted** `{user}`",
								buttons=[[Button.inline("‹ Back ›","recovery")]])
		except:
			await event.respond(f"**Failed to delete user** `{user}`",
								buttons=[[Button.inline("‹ Back ›","recovery")]])
	chat = event.chat_id
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await del_trojan_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)
		
@bot.on(events.CallbackQuery(data=b'delrcss'))
async def del_ss(event):
	async def del_ss_(event):
		cmd = 'cat /etc/xray/.lock.db | grep "^#!!" | cut -d " " -f 2-3 | sort | uniq | nl'.strip()
		x = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
		print(x)
		z = subprocess.check_output(cmd, shell=True).decode("utf-8")
		await event.respond(f"""
**◇━━━━━━━━━━━━━━━━━━◇**
	** ⟨🔸 Delet Recovery🔸⟩**
**◇━━━━━━━━━━━━━━━━━━◇**
```
{z}
```
""")
		async with bot.conversation(chat) as user:
			await event.respond('**Username:**')
			user = user.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			user = (await user).raw_text.replace(" ", "")
		cmd = f'sed -i "/^#!! {user}/d" /etc/xray/.lock.db'
		try:
			subprocess.check_output(cmd, shell=True)
			await event.respond(f"**Successfully Deleted** `{user}`",
								buttons=[[Button.inline("‹ Back ›","recovery")]])
		except:
			await event.respond(f"**Failed to delete user** `{user}`",
								buttons=[[Button.inline("‹ Back ›","recovery")]])
	chat = event.chat_id
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await del_ss_(event)
	else:
		await event.answer("Akses Ditolak",alert=True)


@bot.on(events.CallbackQuery(data=b'recovery'))
async def vmess(event):
	async def vmess_(event):
		inline = [
[Button.inline(" DEL VM LOCK ","delrcvm"),
Button.inline(" DEL VL LOCK","delrcvl")],
[Button.inline(" DEL TR LOCK","delrctr"),
Button.inline(" DEL SS LOCK ","delrcss")],
[Button.inline("‹ Main Menu ›","menu")]]
		z = requests.get(f"http://ip-api.com/json/?fields=country,region,city,timezone,isp").json()
		msg = f"""
**◇━━━━━━━━━━━━━━━━━━━━━━━◇** 
**⚡️ DELET LOCK MANAGER ⚡️**
**◇━━━━━━━━━━━━━━━━━━━━━━━◇** 
**»🔰Hostname/IP:** `{DOMAIN}`
**»🔰ISP:** `{z["isp"]}`
**»🔰Country:** `{z["country"]}`
**◇━━━━━━━━━━━━━━━━━━━━━━━◇** 
"""
		await event.edit(msg,buttons=inline)
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await vmess_(event)
	else:
		await event.answer("Access Denied",alert=True)

