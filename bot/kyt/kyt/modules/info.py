from kyt import *
#CEK VMESS
@bot.on(events.CallbackQuery(data=b'info'))
async def info_vps(event):
	async def info_vps_(event):
		msg = await event.respond("**🔄Proses sedang berjalan...**")
		cmd = 'bot-vps-info'.strip()
		x = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
		print(x)
		z = subprocess.check_output(cmd, shell=True).decode("utf-8")
		await event.respond(f"""```{z}```
**🤖@WendiVpn**
""",buttons=[[Button.inline("‹ Main Menu ›","menu")]])
		await msg.delete()  # Tambahkan ini untuk menghapus pesan setelah proses selesai
	sender = await event.get_sender()
	a = valid(str(sender.id))
	if a == "true":
		await info_vps_(event)
	else:
		await event.answer("Access Denied",alert=True)