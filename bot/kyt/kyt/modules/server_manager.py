import paramiko
import re
from kyt import *

SSH_KEY_DIR = "/etc/kyt/keys"

def _ensure_key_dir():
	os.makedirs(SSH_KEY_DIR, exist_ok=True)
	os.chmod(SSH_KEY_DIR, 0o700)

def _init_servers_table():
	db = get_db()
	db.execute("""CREATE TABLE IF NOT EXISTS servers (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		name TEXT NOT NULL,
		host TEXT NOT NULL,
		port INTEGER DEFAULT 22,
		username TEXT DEFAULT 'root',
		auth_type TEXT DEFAULT 'password',
		password TEXT DEFAULT '',
		key_file TEXT DEFAULT '',
		status TEXT DEFAULT 'unknown',
		created_at TEXT DEFAULT (datetime('now','localtime'))
	)""")
	db.commit()

_init_servers_table()

def get_servers():
	db = get_db()
	return db.execute("SELECT * FROM servers ORDER BY name ASC").fetchall()

def get_server(sid):
	db = get_db()
	return db.execute("SELECT * FROM servers WHERE id=?", (sid,)).fetchone()

def add_server(name, host, port, username, password):
	db = get_db()
	db.execute(
		"INSERT INTO servers (name,host,port,username,password) VALUES (?,?,?,?,?)",
		(name, host, port, username, password)
	)
	db.commit()
	return db.execute("SELECT last_insert_rowid()").fetchone()[0]

def delete_server(sid):
	db = get_db()
	db.execute("DELETE FROM servers WHERE id=?", (sid,))
	db.commit()

def update_server_status(sid, status):
	db = get_db()
	db.execute("UPDATE servers SET status=? WHERE id=?", (status, sid))
	db.commit()

def exec_ssh(host, port, username, password, command, timeout=60):
	client = paramiko.SSHClient()
	client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	try:
		client.connect(
			hostname=host,
			port=port,
			username=username,
			password=password,
			timeout=15
		)
		stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
		output = stdout.read().decode('utf-8', errors='ignore')
		error = stderr.read().decode('utf-8', errors='ignore')
		rc = stdout.channel.recv_exit_status()
		return {"success": rc == 0, "output": output, "error": error, "rc": rc}
	except Exception as e:
		return {"success": False, "output": "", "error": str(e), "rc": -1}
	finally:
		client.close()

def test_server_connection(sid):
	s = get_server(sid)
	if not s:
		return {"success": False, "error": "Server not found"}
	r = exec_ssh(s["host"], s["port"], s["username"], s["password"],
		"echo OK && cat /etc/os-release 2>/dev/null | grep PRETTY_NAME | head -1")
	if r["success"]:
		m = re.search(r'PRETTY_NAME="(.+)"', r["output"])
		os_name = m.group(1) if m else "Unknown"
		update_server_status(sid, "online")
		return {"success": True, "os": os_name}
	else:
		update_server_status(sid, "offline")
		return {"success": False, "error": r["error"] or r["output"]}

def run_on_server(sid, command):
	s = get_server(sid)
	if not s:
		return {"success": False, "output": "", "error": "Server not found"}
	return exec_ssh(s["host"], s["port"], s["username"], s["password"], command)

# ── Bot Callbacks ──────────────────────────────────────────────────────

@bot.on(events.CallbackQuery(data=b'adm-servers'))
async def adm_servers_menu(event):
	sender = await event.get_sender()
	if valid(str(sender.id)) != "true":
		return
	servers = get_servers()
	btns = []
	for s in servers:
		icon = "🟢" if s["status"] == "online" else "🔴"
		btns.append([Button.inline(f"{icon} {s['name']} ({s['host']})", f"svr-view-{s['id']}".encode())])
	btns.append([Button.inline("➕ Tambah Server","svr-add")])
	btns.append([Button.inline("‹ Back","setting")])
	msg = "**🌐 SERVER MANAGEMENT**\n\n"
	if not servers:
		msg += "Belum ada server terdaftar.\nTambahkan server VPS untuk mengelola akun dari jarak jauh."
	else:
		msg += f"Total: {len(servers)} server"
	await event.edit(msg, buttons=btns)

@bot.on(events.CallbackQuery(func=lambda e: e.data.startswith(b'svr-view-')))
async def adm_server_view(event):
	sender = await event.get_sender()
	if valid(str(sender.id)) != "true":
		return
	sid = int(event.data.decode().replace('svr-view-',''))
	s = get_server(sid)
	if not s:
		await event.answer("Server not found", alert=True)
		return
	await event.edit(
		f"**📡 Server: {s['name']}**\n\n"
		f"Host: `{s['host']}:{s['port']}`\n"
		f"User: `{s['username']}`\n"
		f"Status: {'🟢 Online' if s['status'] == 'online' else '🔴 Offline'}\n"
		f"Ditambahkan: {s['created_at']}",
		buttons=[
			[Button.inline("🔄 Test Koneksi",f"svr-test-{sid}".encode())],
			[Button.inline("🗑️ Hapus",f"svr-del-{sid}".encode())],
			[Button.inline("‹ Kembali","adm-servers")]
		]
	)

@bot.on(events.CallbackQuery(func=lambda e: e.data.startswith(b'svr-test-')))
async def adm_server_test(event):
	sender = await event.get_sender()
	if valid(str(sender.id)) != "true":
		return
	sid = int(event.data.decode().replace('svr-test-',''))
	await event.answer("⏳ Testing koneksi...", alert=False)
	r = test_server_connection(sid)
	s = get_server(sid)
	status_icon = "🟢" if s["status"] == "online" else "🔴"
	msg = f"**📡 Server: {s['name']}**\n\n"
	if r["success"]:
		msg += f"✅ **Koneksi Berhasil**\nOS: `{r['os']}`"
	else:
		msg += f"❌ **Koneksi Gagal**\nError: `{r['error']}`"
	msg += f"\n\nStatus: {status_icon} {s['status'].upper()}"
	await event.edit(msg, buttons=[
		[Button.inline("🔄 Test Ulang",f"svr-test-{sid}".encode())],
		[Button.inline("‹ Kembali","adm-servers")]
	])

@bot.on(events.CallbackQuery(func=lambda e: e.data.startswith(b'svr-del-')))
async def adm_server_del(event):
	sender = await event.get_sender()
	if valid(str(sender.id)) != "true":
		return
	sid = int(event.data.decode().replace('svr-del-',''))
	s = get_server(sid)
	if not s:
		return
	await event.edit(
		f"⚠️ **Hapus server `{s['name']}`?**\n\n"
		f"Host: {s['host']}\n\n"
		"Tindakan ini tidak bisa dibatalkan.",
		buttons=[
			[Button.inline("✅ Ya, Hapus",f"svr-delc-{sid}".encode())],
			[Button.inline("❌ Batal","adm-servers")]
		]
	)

@bot.on(events.CallbackQuery(func=lambda e: e.data.startswith(b'svr-delc-')))
async def adm_server_delc(event):
	sender = await event.get_sender()
	if valid(str(sender.id)) != "true":
		return
	sid = int(event.data.decode().replace('svr-delc-',''))
	s = get_server(sid)
	if s:
		delete_server(sid)
		await event.answer(f"Server {s['name']} dihapus", alert=True)
	await adm_servers_menu(event)

@bot.on(events.CallbackQuery(data=b'svr-add'))
async def adm_server_add(event):
	sender = await event.get_sender()
	if valid(str(sender.id)) != "true":
		return
	chat = event.chat_id
	try:
		async with bot.conversation(chat) as c1:
			await event.respond("**Masukkan NAMA server:**\n_Contoh: VPS Singapore 1_")
			r1 = await c1.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			name = r1.raw_text.strip()
		async with bot.conversation(chat) as c2:
			await event.respond("**Masukkan HOST/IP server:**")
			r2 = await c2.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			host = r2.raw_text.strip()
		async with bot.conversation(chat) as c3:
			await event.respond("**Masukkan PORT SSH** (default: 22):")
			r3 = await c3.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			port = int(r3.raw_text.strip()) if r3.raw_text.strip().isdigit() else 22
		async with bot.conversation(chat) as c4:
			await event.respond("**Masukkan USERNAME** (default: root):")
			r4 = await c4.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			username = r4.raw_text.strip() or "root"
		async with bot.conversation(chat) as c5:
			await event.respond("**Masukkan PASSWORD SSH:**")
			r5 = await c5.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
			password = r5.raw_text.strip()
		sid = add_server(name, host, port, username, password)
		await event.respond(f"✅ **Server ditambahkan!**\n\n`{name}` (`{host}:{port}`)\n\n⏳ Test koneksi...")
		r = test_server_connection(sid)
		s = get_server(sid)
		status = "🟢 Online" if s["status"] == "online" else "🔴 Offline"
		extra = ""
		if r["success"]:
			extra = f"\nOS: `{r['os']}`"
		else:
			extra = f"\nError: `{r['error']}`"
		await event.respond(
			f"**📡 {name}**\n\n"
			f"Status: {status}{extra}",
			buttons=[[Button.inline("‹ Kelola Server","adm-servers")]]
		)
	except Exception as e:
		await event.respond(f"❌ Gagal: `{e}`")
