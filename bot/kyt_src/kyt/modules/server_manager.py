import paramiko
import re
from kyt import *

SSH_KEY_DIR = "/etc/kyt/keys"

def _ensure_key_dir():
    os.makedirs(SSH_KEY_DIR, exist_ok=True)
    os.chmod(SSH_KEY_DIR, 0o700)

def _init_servers_table():
    db = get_db()
    try:
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
    finally:
        db.close()

# ── CATATAN KEAMANAN (batch 2) ──────────────────────────────────────────
# Kolom `password` di tabel `servers` menyimpan password SSH dalam PLAINTEXT.
# Risiko: siapa pun yang membaca file kyt/database.db mendapatkan akses root
# ke semua server terdaftar. Mitigasi yang disarankan:
#   1. Gunakan auth_type='key' + key_file (kolom sudah tersedia) alih-alih password.
#   2. Batasi permission file database (600) dan hanya di VPS admin.
# Enkripsi kolom tidak diterapkan karena tidak ada library kriptografi di
# requirements (menambah dependency butuh install di semua VPS + migrasi data
# plaintext yang sudah ada) — ditandai PENDING di laporan batch 2.

_init_servers_table()

def get_servers():
    db = get_db()
    try:
        return db.execute("SELECT * FROM servers ORDER BY name ASC").fetchall()
    finally:
        db.close()

def get_server(sid):
    db = get_db()
    try:
        return db.execute("SELECT * FROM servers WHERE id=?", (sid,)).fetchone()
    finally:
        db.close()

def add_server(name, host, port, username, password):
    db = get_db()
    try:
        db.execute(
            "INSERT INTO servers (name,host,port,username,password) VALUES (?,?,?,?,?)",
            (name, host, port, username, password)
        )
        db.commit()
        return db.execute("SELECT last_insert_rowid()").fetchone()[0]
    finally:
        db.close()

def delete_server(sid):
    db = get_db()
    try:
        db.execute("DELETE FROM servers WHERE id=?", (sid,))
        db.commit()
    finally:
        db.close()

def update_server_status(sid, status):
    db = get_db()
    try:
        db.execute("UPDATE servers SET status=? WHERE id=?", (status, sid))
        db.commit()
    finally:
        db.close()

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

# ── Active Server per-user ──────────────────────────────────────────────

_active_servers = {}  # telegram_id_str -> server_id (int SSH) or None
_active_api_servers = {}  # telegram_id_str -> remote_server_id (int) or None

def set_active(tid, sid):
    _active_servers[tid] = sid

def get_active(tid):
    return _active_servers.get(tid)

def set_active_api(tid, sid):
    _active_api_servers[tid] = sid

def get_active_api(tid):
    return _active_api_servers.get(tid)

def exec_cmd(cmd, tid=None, timeout=60):
    import subprocess as _sp
    if tid:
        # 1. Try remote API server
        api_sid = get_active_api(tid)
        if api_sid is not None:
            s = get_remote_server(api_sid)
            if s:
                mapped = api_map_account_command(cmd)
                if mapped:
                    result = api_call_remote(api_sid, mapped[0], mapped[1], timeout=timeout, no_notif=True)
                    return result.encode("utf-8")
                mapped = api_map_maintenance_command(cmd)
                if mapped:
                    result = api_call_remote(api_sid, mapped[0], mapped[1], timeout=timeout, no_notif=False)
                    return result.encode("utf-8")
        # 2. Try SSH server
        sid = get_active(tid)
        if sid is not None:
            r = run_on_server(sid, cmd)
            if not r["success"]:
                raise _sp.CalledProcessError(r["rc"], cmd, output=r["output"].encode())
            return r["output"].encode()
    # 3. Local via API mapping
    mapped = api_map_account_command(cmd)
    if mapped:
        return api_account_command(cmd, timeout=timeout).encode("utf-8")
    mapped = api_map_maintenance_command(cmd)
    if mapped:
        return api_maintenance_command(cmd, timeout=timeout).encode("utf-8")
    return _sp.check_output(cmd, shell=True, timeout=timeout)

# ── Bot Callbacks ──────────────────────────────────────────────────────

@bot.on(events.CallbackQuery(data=b'adm-servers'))
async def adm_servers_menu(event):
    sender = await event.get_sender()
    if valid(str(sender.id)) != "true":
        return
    tid = str(sender.id)
    active = get_active(tid)
    servers = get_servers()
    btns = []
    for s in servers:
        icon = "🟢" if s["status"] == "online" else "🔴"
        label = f"{icon} {s['name']} ({s['host']})"
        if active == s['id']:
            label = f"🎯 {label}"
        btns.append([Button.inline(label, f"svr-view-{s['id']}".encode())])
    btns.append([Button.inline("➕ Tambah Server","svr-add")])
    if active is not None:
        btns.append([Button.inline("📍 Lokal (nonaktifkan)","svr-active-off".encode())])
    btns.append([Button.inline("‹ Back","setting")])
    msg = "**🌐 SERVER MANAGEMENT**\n\n"
    if not servers:
        msg += "Belum ada server terdaftar.\nTambahkan server VPS untuk mengelola akun dari jarak jauh."
    else:
        msg += f"Total: {len(servers)} server"
    if active is not None:
        sname = get_server(active)["name"] if get_server(active) else "?"
        msg += f"\n\n🎯 **Aktif: `{sname}`**\nSemua pembuatan akun akan dikirim ke server ini."
    else:
        msg += "\n\n📍 **Aktif: Lokal**\nAkun dibuat di VPS ini."
    await event.edit(msg, buttons=btns)

@bot.on(events.CallbackQuery(func=lambda e: e.data.startswith(b'svr-view-')))
async def adm_server_view(event, sid=None):
    sender = await event.get_sender()
    if valid(str(sender.id)) != "true":
        return
    if sid is None:
        sid = int(event.data.decode().replace('svr-view-',''))
    s = get_server(sid)
    if not s:
        await event.answer("Server not found", alert=True)
        return
    sender = await event.get_sender()
    tid = str(sender.id)
    active = get_active(tid)
    act_btn_text = "📍 Set Active" if active != s['id'] else "✅ Active"
    await event.edit(
        f"**📡 Server: {s['name']}**\n\n"
        f"Host: `{s['host']}:{s['port']}`\n"
        f"User: `{s['username']}`\n"
        f"Status: {'🟢 Online' if s['status'] == 'online' else '🔴 Offline'}\n"
        f"Ditambahkan: {s['created_at']}",
        buttons=[
            [Button.inline(act_btn_text,f"svr-setact-{sid}".encode())],
            [Button.inline("🔄 Test Koneksi",f"svr-test-{sid}".encode())],
            [Button.inline("🗑️ Hapus",f"svr-del-{sid}".encode())],
            [Button.inline("‹ Kembali","adm-servers")]
        ]
    )

@bot.on(events.CallbackQuery(func=lambda e: e.data.startswith(b'svr-setact-')))
async def adm_server_setact(event):
    sender = await event.get_sender()
    if valid(str(sender.id)) != "true":
        return
    tid = str(sender.id)
    sid = int(event.data.decode().replace('svr-setact-',''))
    s = get_server(sid)
    if not s:
        await event.answer("Server not found", alert=True)
        return
    set_active(tid, sid)
    await event.answer(f"✅ Active server: {s['name']}", alert=True)
    await adm_server_view(event, sid=sid)

@bot.on(events.CallbackQuery(data=b'svr-active-off'))
async def adm_server_active_off(event):
    sender = await event.get_sender()
    if valid(str(sender.id)) != "true":
        return
    tid = str(sender.id)
    set_active(tid, None)
    await event.answer("📍 Active: Lokal", alert=True)
    await adm_servers_menu(event)

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

# ── REMOTE API SERVER MANAGEMENT ──────────────────────────────────────────────

_build_servers_keyboard = lambda servers: [
    [Button.inline(f"{'🟢' if s['status']=='online' else '🔴'} {s['name']}  | {s['url'][:40]}", f"adm-api-detail-{s['id']}")]
    for s in servers
]

@bot.on(events.CallbackQuery(data=b'adm-api-servers'))
async def adm_api_servers(event):
    async def _inner(event):
        servers = get_remote_servers()
        if not servers:
            await event.edit("**🌐 Remote API Servers**\n\nBelum ada server.\n\nGunakan button di bawah untuk menambah server remote.", buttons=[
                [Button.inline("➕ Tambah","adm-api-add")],
                [Button.inline("‹ Kembali","setting")]
            ])
            return
        text = "**🌐 Remote API Servers**\n\n"
        for s in servers:
            text += f"{'🟢' if s['status']=='online' else '🔴'} **{s['name']}**\n`{s['url'][:60]}`\n"
        await event.edit(text, buttons=_build_servers_keyboard(servers) + [
            [Button.inline("➕ Tambah","adm-api-add")],
            [Button.inline("‹ Kembali","setting")]
        ])
    sender = await event.get_sender()
    if valid(str(sender.id)) != "true":
        await event.answer("Access Denied", alert=True)
        return
    await _inner(event)

@bot.on(events.CallbackQuery(pattern=b'adm-api-detail-(\\d+)'))
async def adm_api_detail(event):
    async def _inner(event):
        sid = int(event.pattern_match.group(1))
        s = get_remote_server(sid)
        if not s:
            await event.answer("Server tidak ditemukan", alert=True)
            return
        active = get_active_api(str(event.sender_id))
        label = "✅ Aktif" if active == sid else "❌ Tidak Aktif"
        text = (
            f"**📡 {s['name']}**\n\n"
            f"URL: `{s['url']}`\n"
            f"Token: `{s['token'][:8]}...{s['token'][-4:]}`\n"
            f"Status: {'🟢 Online' if s['status']=='online' else '🔴 Offline'}\n"
            f"Aktif: {label}\n"
        )
        buttons = [
            [Button.inline("🔍 Test", f"adm-api-test-{sid}"),
             Button.inline("✅ Set Active", f"adm-api-activate-{sid}")],
            [Button.inline("🔗 Sync Bot", f"adm-api-sync-{sid}"),
             Button.inline("🗑️ Hapus", f"adm-api-delete-{sid}")],
            [Button.inline("‹ Kembali", "adm-api-servers")]
        ]
        await event.edit(text, buttons=buttons)
    sender = await event.get_sender()
    if valid(str(sender.id)) != "true":
        await event.answer("Access Denied", alert=True)
        return
    await _inner(event)

@bot.on(events.CallbackQuery(pattern=b'adm-api-test-(\\d+)'))
async def adm_api_test(event):
    async def _inner(event):
        sid = int(event.pattern_match.group(1))
        await event.answer("Menguji koneksi...", alert=False)
        r = test_remote_server(sid)
        if r["ok"]:
            await event.edit(
                "✅ **Koneksi Berhasil**\n\nServer remote merespon dengan baik.",
                buttons=[[Button.inline("‹ Kembali", f"adm-api-detail-{sid}")]]
            )
        else:
            await event.edit(
                f"❌ **Gagal terkoneksi**\n\n`{r.get('error','unknown error')}`",
                buttons=[[Button.inline("‹ Kembali", f"adm-api-detail-{sid}")]]
            )
    sender = await event.get_sender()
    if valid(str(sender.id)) != "true":
        await event.answer("Access Denied", alert=True)
        return
    await _inner(event)

@bot.on(events.CallbackQuery(pattern=b'adm-api-activate-(\\d+)'))
async def adm_api_activate(event):
    async def _inner(event):
        sid = int(event.pattern_match.group(1))
        s = get_remote_server(sid)
        if not s:
            await event.answer("Server tidak ditemukan", alert=True)
            return
        set_active_api(str(event.sender_id), sid)
        set_active(str(event.sender_id), None)  # deactivate SSH server
        # Auto-push bot config
        sync_note = ""
        try:
            base = s["url"].rstrip("/")
            headers = {"X-API-Token": s["token"], "Content-Type": "application/json"}
            payload = {"bot_token": BOT_TOKEN, "chat_id": str(event.sender_id)}
            requests.post(f"{base}/api/system/bot-config", json=payload, headers=headers, timeout=15)
            sync_note = "\n✅ Bot config tersinkronisasi."
        except Exception:
            sync_note = "\n⚠️ Gagal sinkronisasi bot config."
        await event.answer(f"✅ Active server: {s['name']}", alert=True)
        await event.edit(
            f"✅ **{s['name']}** sekarang aktif!{sync_note}\nSemua perintah akan dijalankan di server remote ini.",
            buttons=[[Button.inline("‹ Kembali", f"adm-api-detail-{sid}")]]
        )
    sender = await event.get_sender()
    if valid(str(sender.id)) != "true":
        await event.answer("Access Denied", alert=True)
        return
    await _inner(event)

@bot.on(events.CallbackQuery(data=b'adm-api-deactivate'))
async def adm_api_deactivate(event):
    async def _inner(event):
        set_active_api(str(event.sender_id), None)
        await event.answer("✅ Remote API server dinonaktifkan. Kembali ke local/SSH mode.", alert=True)
    sender = await event.get_sender()
    if valid(str(sender.id)) != "true":
        await event.answer("Access Denied", alert=True)
        return
    await _inner(event)

@bot.on(events.CallbackQuery(pattern=b'adm-api-sync-(\\d+)'))
async def adm_api_sync_bot(event):
    async def _inner(event):
        sid = int(event.pattern_match.group(1))
        s = get_remote_server(sid)
        if not s:
            await event.answer("Server tidak ditemukan", alert=True)
            return
        await event.edit("**🔄 Mengirim konfigurasi bot ke server remote...**")
        try:
            base = s["url"].rstrip("/")
            headers = {
                "X-API-Token": s["token"],
                "Content-Type": "application/json",
            }
            payload = {
                "bot_token": BOT_TOKEN,
                "chat_id": str(event.sender_id),
            }
            resp = requests.post(f"{base}/api/system/bot-config", json=payload, headers=headers, timeout=15)
            data = resp.json()
            if data.get("ok"):
                await event.edit(
                    "✅ **Konfigurasi bot berhasil disinkronisasi!**\n\n"
                    f"Semua notifikasi dari `{s['name']}` akan menggunakan bot token yang sama.",
                    buttons=[[Button.inline("‹ Kembali", f"adm-api-detail-{sid}")]]
                )
            else:
                await event.edit(
                    f"❌ **Gagal**: {data.get('error', 'unknown error')}",
                    buttons=[[Button.inline("‹ Kembali", f"adm-api-detail-{sid}")]]
                )
        except Exception as e:
            await event.edit(
                f"❌ **Gagal terkoneksi**: `{e}`",
                buttons=[[Button.inline("‹ Kembali", f"adm-api-detail-{sid}")]]
            )
    sender = await event.get_sender()
    if valid(str(sender.id)) != "true":
        await event.answer("Access Denied", alert=True)
        return
    await _inner(event)

@bot.on(events.CallbackQuery(pattern=b'adm-api-delete-(\\d+)'))
async def adm_api_delete(event):
    async def _inner(event):
        sid = int(event.pattern_match.group(1))
        s = get_remote_server(sid)
        if s:
            delete_remote_server(sid)
            await event.answer(f"🗑️ {s['name']} dihapus", alert=True)
        await event.edit("✅ **Server dihapus**", buttons=[[Button.inline("‹ Kembali", "adm-api-servers")]])
    sender = await event.get_sender()
    if valid(str(sender.id)) != "true":
        await event.answer("Access Denied", alert=True)
        return
    await _inner(event)

@bot.on(events.CallbackQuery(data=b'adm-api-add'))
async def adm_api_add(event):
    async def _inner(event):
        sender = await event.get_sender()
        chat = event.chat_id
        async with bot.conversation(chat) as c1:
            await event.edit("**➕ Tambah Remote API Server**\n\nMasukkan **Nama** server (label, misal: `VPS SG`):")
            r1 = await c1.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
            name = r1.raw_text.strip()
        async with bot.conversation(chat) as c2:
            await event.edit("Masukkan **URL** server:\nContoh: `https://ip-anda:8443`")
            r2 = await c2.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
            url = r2.raw_text.strip()
        async with bot.conversation(chat) as c3:
            await event.edit("Masukkan **API Token** (sama dengan `api_token` di panel):")
            r3 = await c3.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
            token = r3.raw_text.strip()
        sid = add_remote_server(name, url, token)
        r = test_remote_server(sid)
        status = "🟢 Online" if r["ok"] else f"🔴 Offline ({r.get('error','?')})"
        # Auto-push bot config if server is online
        sync_status = ""
        if r["ok"]:
            try:
                base = url.rstrip("/")
                headers = {"X-API-Token": token, "Content-Type": "application/json"}
                payload = {"bot_token": BOT_TOKEN, "chat_id": str(sender.id)}
                requests.post(f"{base}/api/system/bot-config", json=payload, headers=headers, timeout=15)
                sync_status = "\n✅ Bot config otomatis tersinkronisasi."
            except Exception:
                sync_status = "\n⚠️ Gagal sinkronisasi bot config. klik '🔗 Sync Bot' di detail."
        await event.edit(
            f"✅ **Server ditambahkan!**\n\nNama: `{name}`\nURL: `{url}`\nStatus: {status}{sync_status}\n\nUji koneksi dari menu detail server.",
            buttons=[[Button.inline("‹ Kelola Server","adm-api-servers")]]
        )
    sender = await event.get_sender()
    if valid(str(sender.id)) != "true":
        await event.answer("Access Denied", alert=True)
        return
    await _inner(event)
