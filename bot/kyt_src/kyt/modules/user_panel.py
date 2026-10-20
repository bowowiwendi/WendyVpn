from kyt import *
from kyt.modules.p2p_pay import create_payment, add_pending
import shutil

# ── CONSTANTS ─────────────────────────────────────────────────────────
SVC_EMOJI = {'ssh':'🔐','vmess':'📡','vless':'🔷','trojan':'🔰','shadowsocks':'🌑'}
SVC_LABEL = {'ssh':'SSH OVPN','vmess':'VMess','vless':'VLess','trojan':'Trojan','shadowsocks':'Shadowsocks'}
SVC_FILE  = {'ssh':'ssh','vmess':'vmess','vless':'vless','trojan':'trojan','shadowsocks':'ss'}

# ── HELPERS ───────────────────────────────────────────────────────────
async def is_group_member(user_id):
    try:
        gid = globals().get('GROUP_ID', '0')
        if not gid or str(gid) == '0':
            return True
        await bot.get_permissions(int(gid), user_id)
        return True
    except:
        return False

def gen_username(svc):
    pfx = {'ssh':'SSH','vmess':'VMS','vless':'VLS','trojan':'TRJ','shadowsocks':'SDS'}
    return f"{pfx.get(svc,'USR')}{random.randint(10000,99999)}"

def gen_password():
    return f"kyt{random.randint(10000,99999)}"

def gen_quota():
    return "100"

async def _kill_trial_later(svc, username, delay=3600):
    """Hapus akun trial setelah delay (fallback bila perintah `at` tidak ada)."""
    await asyncio.sleep(delay)
    try:
        api_delete_account(svc, username, timeout=30)
    except Exception:
        pass

def _schedule_trial_kill(svc, username):
    """Jadwalkan penghapusan akun trial 1 jam lagi. Pakai `at` bila tersedia;
    bila tidak ada/gagal, pakai asyncio fallback agar trial tidak kebablasan
    hidup 24 jam (days=1 di API)."""
    kill_proto = TRIAL_SCRIPT.get(svc, svc)
    try:
        if shutil.which("at"):
            r = subprocess.run(
                f'echo "killtrial {kill_proto} {shlex.quote(username)}" | at now + 60 minutes',
                shell=True, timeout=10)
            if r.returncode == 0:
                return True
    except Exception:
        pass
    asyncio.create_task(_kill_trial_later(svc, username))
    return False

async def notify_admin(msg):
    try:
        await bot.send_message(int(ADMIN), msg)
    except:
        pass

async def show_panel(event, sender):
    tid = str(sender.id)
    ensure_user_exists(tid, sender.username or '')
    bal = get_balance(tid)
    svcs = get_user_services(tid)
    sn = globals().get('STORE_NAME', '🏪 Store')
    name = sender.first_name or sender.username or "User"
    msg = (
        f"👤 **PANEL USER**\n\n"
        f"Halo, **{name}**!\n{sn}\n\n"
        f"💰 **Saldo** : `{format_rupiah(bal)}`\n"
        f"📦 **Layanan** : `{len(svcs)}` akun\n"
        f"🌐 **Server** : `{DOMAIN}`"
    )
    trial_ok = can_claim_trial(tid)
    ac = globals().get('ADMIN_CONTACT', 'https://t.me/WendiVpn')
    btns = [
        [Button.inline("💰 Saldo","up-saldo"),
         Button.inline("🛒 Beli Layanan","up-beli")],
        [Button.inline("🎁 Trial Gratis" if trial_ok else "✅ Trial Hari Ini","up-trial" if trial_ok else "dummy"),
         Button.inline("📋 Layanan Saya","up-layanan")],
        [Button.inline("🔄 Minta Renew","up-renew"),
         Button.inline("📋 Daftar Harga","up-price")],
        [Button.inline("ℹ️ Info Server","up-server")],
        [Button.url("📞 Hubungi Admin", ac)]
    ]
    try:
        await event.edit(msg, buttons=btns)
    except:
        await event.respond(msg, buttons=btns)

# ── /start ────────────────────────────────────────────────────────────
@bot.on(events.NewMessage(pattern=r'/start$'))
async def start_cmd(event):
    sender = await event.get_sender()
    tid = str(sender.id)
    if valid(tid) == "true":
        from kyt.modules.menu import menu
        await menu(event)
        return
    if not await is_group_member(sender.id):
        await event.respond(
            "❌ **Akses Ditolak**\n\n"
            "Bergabunglah ke grup kami terlebih dahulu,\nlalu kirim /start lagi.")
        return
    await show_panel(event, sender)

@bot.on(events.CallbackQuery(data=b'up-main'))
async def up_main(event):
    sender = await event.get_sender()
    await show_panel(event, sender)

# ── DAFTAR HARGA ───────────────────────────────────────────────────────
@bot.on(events.CallbackQuery(data=b'up-price'))
async def up_price(event):
    lines = "**📋 DAFTAR HARGA**\n\n"
    for svc in ['ssh','vmess','vless','trojan','shadowsocks']:
        prices = get_service_prices(svc)
        emoji = SVC_EMOJI.get(svc, '🔧')
        label = SVC_LABEL.get(svc, svc.upper())
        lines += f"{emoji} **{label}**\n"
        for dur, price in prices:
            lines += f"   `{dur:>2} hari` — `{format_rupiah(price)}`\n"
        lines += "\n"
    lines += "💳 **Top Up** dulu untuk membeli."
    await event.edit(lines, buttons=[[Button.inline("‹ Back","up-main")]])

# ── SALDO ─────────────────────────────────────────────────────────────
@bot.on(events.CallbackQuery(data=b'up-saldo'))
async def up_saldo(event):
    sender = await event.get_sender()
    tid = str(sender.id)
    bal = get_balance(tid)
    db = get_db()
    txs = db.execute(
        "SELECT type,amount,description,created_at FROM transactions "
        "WHERE telegram_id=? ORDER BY created_at DESC LIMIT 5", (tid,)
    ).fetchall()
    tx_lines = ""
    if txs:
        tx_lines = "\n**◇━━━━━━━━━━◇**\n"
        for t in txs:
            icon = "➕" if t['type'] == 'topup' else "➖"
            tx_lines += f"{icon} `{format_rupiah(t['amount'])}` — {t['description']}\n"
    await event.edit(
        f"💰 **SALDO ANDA**\n\n"
        f"💵 Saldo : `{format_rupiah(bal)}`\n"
        f"🆔 ID    : `{tid}`\n"
        f"{tx_lines}\n",
        buttons=[
            [Button.inline("💳 Top Up QRIS","up-qris")],
            [Button.inline("‹ Back","up-main")]
        ]
    )

# ── QRIS TOP UP ────────────────────────────────────────────────────────
QRIS_AMOUNTS = [1000, 5000, 10000, 25000, 50000]

@bot.on(events.CallbackQuery(data=b'up-qris'))
async def up_qris(event):
    btns = []
    row = []
    for i, amt in enumerate(QRIS_AMOUNTS):
        label = f"Rp{amt//1000}k"
        row.append(Button.inline(label, f"up-qris-{amt}".encode()))
        if len(row) == 2 or i == len(QRIS_AMOUNTS) - 1:
            btns.append(row)
            row = []
    btns.append([Button.inline("‹ Back","up-saldo")])
    await event.edit("💳 **TOP UP VIA QRIS**\n\nPilih nominal:", buttons=btns)

@bot.on(events.CallbackQuery(func=lambda e: e.data.startswith(b'up-qris-')))
async def up_qris_pay(event):
    sender = await event.get_sender()
    tid = str(sender.id)
    amount_str = event.data.decode().replace('up-qris-','')
    try:
        amount = int(amount_str)
    except:
        return
    await event.edit("⏳ Membuat pembayaran...", buttons=None)
    res = create_payment(
        amount=amount,
        description=f"Top Up {format_rupiah(amount)} - {tid}",
        customer_name=tid,
    )
    if not res.get("success"):
        await event.edit(
            f"❌ **Gagal membuat pembayaran**\n\n{res.get('error', 'Unknown error')}",
            buttons=[[Button.inline("‹ Coba Lagi","up-qris")]]
        )
        return
    data = res.get("data") or res
    invoice_id = data.get("invoice_id", "")
    if not invoice_id:
        await event.edit(
            "❌ **Gagal: invoice_id tidak ditemukan**",
            buttons=[[Button.inline("‹ Coba Lagi","up-qris")]]
        )
        return
    add_pending(tid, invoice_id, amount)
    payment_url = data.get("payment_url", "")
    qris_string = data.get("qris_dynamic_string", "") or data.get("qris_string", "")
    qris_image_url = data.get("qris_dynamic_image_url") or data.get("qris_static_image_url", "")
    msg = (
        f"💳 **Pembayaran QRIS**\n\n"
        f"💰 Nominal: `{format_rupiah(amount)}`\n"
        f"📄 Invoice: `{invoice_id}`\n"
        f"⏳ Status: **Pending**\n\n"
        f"**Cara bayar:**\n"
        f"1. Scan QRIS di bawah via aplikasi e-wallet (GoPay/OVO/DANA/dll)\n"
        f"2. Saldo akan otomatis bertambah setelah pembayaran terkonfirmasi\n\n"
        f"_Menunggu pembayaran..._"
    )
    btns = [
        [Button.inline("🔄 Cek Status","up-qris-cek"),
         Button.inline("❌ Batal","up-qris-batal")]
    ]
    try:
        await event.delete()
    except:
        pass
    qr_sent = False
    if qris_image_url:
        local_img = download_qr_image(qris_image_url, f"qris_{invoice_id}")
        if local_img:
            try:
                await bot.send_file(event.chat_id, local_img, caption=msg, buttons=btns)
                os.unlink(local_img)
                qr_sent = True
            except:
                try:
                    os.unlink(local_img)
                except:
                    pass
    if not qr_sent:
        try:
            qr_input = qris_string or payment_url
            p = generate_qr(qr_input, f"qris_{invoice_id}")
            if p:
                await bot.send_file(event.chat_id, p, caption=msg, buttons=btns)
                os.unlink(p)
                qr_sent = True
            else:
                await bot.send_message(event.chat_id, msg, buttons=btns)
                qr_sent = True
        except:
            pass
    if not qr_sent:
        try:
            await bot.send_message(event.chat_id, msg, buttons=btns)
        except:
            pass

@bot.on(events.CallbackQuery(data=b'up-qris-cek'))
async def up_qris_cek(event):
    await event.answer("Saldo otomatis bertambah dalam beberapa menit setelah pembayaran dikonfirmasi. Silakan cek saldo via menu Saldo.", alert=True)

@bot.on(events.CallbackQuery(data=b'up-qris-batal'))
async def up_qris_batal(event):
    await event.edit("❌ Pembayaran dibatalkan.",
        buttons=[[Button.inline("‹ Kembali","up-saldo")]])

# ── BELI LAYANAN ──────────────────────────────────────────────────────
@bot.on(events.CallbackQuery(data=b'up-beli'))
async def up_beli(event):
    await event.edit(
        "🛒 **BELI LAYANAN**\n\nPilih jenis layanan:",
        buttons=[
            [Button.inline("🔐 SSH OVPN","up-buy-ssh"),
             Button.inline("📡 VMess","up-buy-vmess")],
            [Button.inline("🔷 VLess","up-buy-vless"),
             Button.inline("🔰 Trojan","up-buy-trojan")],
            [Button.inline("🌑 Shadowsocks","up-buy-ss")],
            [Button.inline("‹ Back","up-main")]
        ]
    )

@bot.on(events.CallbackQuery(func=lambda e: e.data.startswith(b'up-buy-')))
async def up_buy_svc(event):
    svc = event.data.decode().replace('up-buy-','')
    if svc == 'ss':
        svc = 'shadowsocks'
    prices = get_service_prices(svc)
    emoji = SVC_EMOJI.get(svc,'🔧')
    label = SVC_LABEL.get(svc, svc.upper())
    btns = [[Button.inline(
        f"📅 {r['duration']}hr — {format_rupiah(r['price'])}",
        f"up-cf-{svc}-{r['duration']}"
    )] for r in prices]
    btns.append([Button.inline("‹ Back","up-beli")])
    await event.edit(f"{emoji} **{label}**\n\nPilih durasi:", buttons=btns)

@bot.on(events.CallbackQuery(func=lambda e: e.data.startswith(b'up-cf-')))
async def up_confirm(event):
    data = event.data.decode()
    parts = data.split('-')
    svc = parts[2]
    dur = int(parts[3])
    sender = await event.get_sender()
    db = get_db()
    pr = db.execute("SELECT price FROM service_prices WHERE service=? AND duration=?", (svc, dur)).fetchone()
    if not pr:
        await event.answer("Harga tidak ditemukan.", alert=True)
        return
    price = pr['price']
    bal = get_balance(str(sender.id))
    emoji = SVC_EMOJI.get(svc,'🔧')
    label = SVC_LABEL.get(svc, svc.upper())
    ok = bal >= price
    btns = [[Button.inline("✅ Beli Sekarang", f"up-pay-{svc}-{dur}"),
        Button.inline("❌ Batal","up-beli")]] if ok else [[Button.inline("‹ Back","up-beli")]]
    await event.edit(
        f"🛒 **KONFIRMASI**\n\n"
        f"{emoji} **Layanan** : {label}\n"
        f"📅 **Durasi** : {dur} hari\n"
        f"💵 **Harga** : `{format_rupiah(price)}`\n"
        f"💰 **Saldo** : `{format_rupiah(bal)}`\n\n"
        f"{'✅ Saldo cukup' if ok else '❌ Saldo tidak cukup'}",
        buttons=btns
    )

_purchase_state = {}

def validate_username(uname):
    return bool(re.match(r'^[a-zA-Z0-9_-]{1,32}$', uname))

async def prompt_username(event, chat, state):
    state['step'] = 'username'
    await event.edit("👤 **Masukkan Username:**\n\nKetik username, atau klik 🔀 Acak untuk nama acak.",
        buttons=[[Button.inline("🔀 Acak", "up-rand-uname")], [Button.inline("❌ Batal","up-beli")]])

@bot.on(events.NewMessage(incoming=True))
async def up_handle_username(event):
    chat = event.chat_id
    if chat not in _purchase_state:
        return
    state = _purchase_state[chat]
    if state.get('step') != 'username':
        return
    sender = await event.get_sender()
    if sender.id != state.get('_sender_id'):
        return
    user = event.raw_text.strip().replace(" ", "")
    if not user:
        await event.respond("❌ Username tidak boleh kosong.",
            buttons=[[Button.inline("‹ Kembali","up-beli")]])
        return
    state['username'] = user
    state['random_user'] = not user or user.lower() == "random"
    if not state['random_user'] and not validate_username(user):
        await event.respond("❌ Username hanya boleh huruf, angka, underscore, hyphen (max 32 karakter).",
            buttons=[[Button.inline("🔄 Coba Lagi", "up-beli")]])
        return
    await ask_password(event, chat, state)

@bot.on(events.CallbackQuery(data=b'up-rand-uname'))
async def up_skip_uname(event):
    chat = event.chat_id
    state = _purchase_state.get(chat)
    if not state or state.get('step') != 'username':
        await event.answer()
        return
    state['username'] = 'random'
    state['random_user'] = True
    await event.edit("✅ Username akan dibuat acak.")
    await ask_password(event, chat, state)

async def ask_password(event, chat, state):
    state['step'] = 'password'
    if state['svc'] == 'ssh':
        await event.respond("🔑 **Masukkan Password SSH:**\n\nKetik password, atau klik 🔀 Acak untuk password acak.",
            buttons=[[Button.inline("🔀 Acak", "up-rand-pass")], [Button.inline("❌ Batal","up-beli")]])
    else:
        state['password'] = "random"
        await proceed_purchase(event, chat, state)

@bot.on(events.NewMessage(incoming=True))
async def up_handle_password(event):
    chat = event.chat_id
    if chat not in _purchase_state:
        return
    state = _purchase_state[chat]
    if state.get('step') != 'password':
        return
    sender = await event.get_sender()
    if sender.id != state.get('_sender_id'):
        return
    pw = event.raw_text.strip().replace(" ", "")
    if not pw:
        await event.respond("❌ Password tidak boleh kosong.",
            buttons=[[Button.inline("‹ Kembali","up-beli")]])
        return
    state['password'] = pw
    await proceed_purchase(event, chat, state)

@bot.on(events.CallbackQuery(data=b'up-rand-pass'))
async def up_skip_pass(event):
    chat = event.chat_id
    state = _purchase_state.get(chat)
    if not state or state.get('step') != 'password':
        await event.answer()
        return
    state['password'] = 'random'
    await event.edit("✅ Password akan dibuat acak.")
    await proceed_purchase(event, chat, state)

@bot.on(events.CallbackQuery(func=lambda e: e.data.startswith(b'up-pay-')))
async def up_pay(event):
    data = event.data.decode()
    parts = data.split('-')
    svc = parts[2]
    dur = int(parts[3])
    sender = await event.get_sender()
    tid = str(sender.id)
    db = get_db()
    pr = db.execute("SELECT price FROM service_prices WHERE service=? AND duration=?", (svc, dur)).fetchone()
    if not pr:
        await event.answer("Error.", alert=True)
        return
    price = pr['price']
    chat = event.chat_id
    _purchase_state[chat] = {
        'svc': svc, 'dur': dur, 'price': price,
        'username': None, 'password': None,
        'random_user': False, 'step': None, '_sender_id': sender.id,
    }
    await prompt_username(event, chat, _purchase_state[chat])

async def proceed_purchase(event, chat, state):
    if chat in _purchase_state:
        del _purchase_state[chat]
    svc = state['svc']
    dur = state['dur']
    price = state['price']
    tid = str(state['_sender_id'])
    label = SVC_LABEL.get(svc, svc.upper())
    if not deduct_balance(tid, price, f"Beli {label} {dur}hr"):
        await bot.send_message(chat, "❌ **Saldo tidak cukup!**",
            buttons=[[Button.inline("‹ Kembali","up-beli")]])
        return
    wait_msg = await bot.send_message(chat, "⏳ **Membuat akun...**")
    username = state['username']
    password = state['password']
    random_user = state.get('random_user', False)
    limit_ip = "2"
    done = False
    for attempt in range(5 if random_user else 1):
        uname = (gen_username(svc) if random_user else username)
        if svc == 'ssh':
            pw = (gen_password() if password == "random" else password)
            quota = gen_quota()
            api_kwargs = dict(password=pw, limit_ip=limit_ip, days=dur)
        elif svc in ('vmess', 'vless', 'trojan'):
            pw = (gen_quota() if password == "random" else password)
            quota = pw
            api_kwargs = dict(limit_ip=limit_ip, quota=quota, days=dur)
        else:
            pw = (gen_quota() if password == "random" else password)
            quota = pw
            api_kwargs = dict(limit_ip=limit_ip, quota=quota, days=dur)
        try:
            api_create_account(svc, uname, **api_kwargs, timeout=30)
            username, password = uname, pw
            done = True
            break
        except:
            if random_user:
                continue
            break
    await wait_msg.delete()
    if not done:
        add_balance(tid, price, f"Refund {label}")
        await bot.send_message(chat, "❌ **Gagal membuat akun.**\nSaldo dikembalikan.",
            buttons=[[Button.inline("‹ Back","up-beli")]])
        return
    expired_at = (DT.date.today() + DT.timedelta(days=dur)).strftime('%Y-%m-%d')
    db = get_db()
    db.execute("INSERT INTO user_services (telegram_id,service,username,expired_at) VALUES (?,?,?,?)",
        (tid, svc, username, expired_at))
    db.commit()
    emoji = SVC_EMOJI.get(svc,'🔧')
    fname = SVC_FILE.get(svc, svc)
    if state.get('_uname'):
        tg_ref = f"@{state['_uname']}"
    else:
        try:
            s = await event.get_sender()
            tg_ref = f"@{s.username}" if s.username else f"ID:{tid}"
        except:
            tg_ref = f"ID:{tid}"
    try:
        raw = subprocess.check_output(f'cat /var/www/html/{fname}-{username}.txt', shell=True).decode("utf-8")
        result = f"```\n{raw.strip()}\n```\n💾 [Simpan Akun](https://{DOMAIN}:8443/{fname}-{username}.txt)"
    except:
        result = (
            f"✅ **Akun berhasil dibuat**\n\n"
            f"👤 **Username** : `{username}`\n"
            f"🌐 **Host** : `{DOMAIN}`\n"
            f"💾 [Simpan Akun](https://{DOMAIN}:8443/{fname}-{username}.txt)"
        )
    qr_link = f"https://{DOMAIN}:8443/{fname}-{username}.txt"
    qr_path = generate_qr(qr_link, f"{svc}_{username}")
    try:
        await bot.send_file(int(tid), qr_path, caption=result, buttons=[[Button.inline("‹ Panel Utama","up-main")]])
        os.unlink(qr_path)
    except:
        os.unlink(qr_path)
        try:
            await event.edit(result, buttons=[[Button.inline("‹ Panel Utama","up-main")]])
        except:
            await bot.send_message(chat, result, buttons=[[Button.inline("‹ Panel Utama","up-main")]])
    await notify_admin(
        f"🔔 **PEMBELIAN BARU**\n\n"
        f"👤 {tg_ref} (`{tid}`)\n"
        f"{emoji} **Layanan** : {label}\n"
        f"🏷️ **Username** : `{username}`\n"
        f"📅 **Durasi** : {dur} hari\n"
        f"💵 **Harga** : {format_rupiah(price)}\n"
        f"⏳ **Expired** : {expired_at}"
    )

# ── TRIAL GRATIS ──────────────────────────────────────────────────────
@bot.on(events.CallbackQuery(data=b'up-trial'))
async def up_trial(event):
    sender = await event.get_sender()
    tid = str(sender.id)
    if not can_claim_trial(tid):
        await event.edit("✅ **Kamu sudah mengambil trial hari ini.**\n\nKembali besok untuk trial gratis lagi!",
            buttons=[[Button.inline("‹ Panel Utama","up-main")]])
        return
    msg = (
        "🎁 **TRIAL GRATIS**\n\n"
        "Pilih layanan untuk trial **1 jam**!\n"
        "_Gratis 1x sehari_\n\n"
        "📌 **Syarat:**\n"
        "• 1x per hari per akun\n"
        "• Berlangsung 1 jam\n"
        "• IP limit 2, Quota 100 MB"
    )
    btns = [
        [Button.inline("🔐 SSH OVPN", "up-trl-ssh"),
         Button.inline("📡 VMess", "up-trl-vmess")],
        [Button.inline("🔷 VLess", "up-trl-vless"),
         Button.inline("🔰 Trojan", "up-trl-trojan")],
        [Button.inline("🌑 Shadowsocks", "up-trl-shadowsocks")],
        [Button.inline("‹ Kembali", "up-main")],
    ]
    await event.edit(msg, buttons=btns)

@bot.on(events.CallbackQuery(func=lambda e: e.data.startswith(b'up-trl-')))
async def up_trial_create(event):
    sender = await event.get_sender()
    tid = str(sender.id)
    svc = event.data.decode().split('-', 2)[2]
    if not can_claim_trial(tid):
        await event.edit("✅ **Kamu sudah mengambil trial hari ini.**",
            buttons=[[Button.inline("‹ Panel Utama","up-main")]])
        return
    label = SVC_LABEL.get(svc, svc.upper())
    emoji = SVC_EMOJI.get(svc, '🔧')
    fname = SVC_FILE.get(svc, svc)
    username = gen_username(svc)
    password = gen_password()
    limit_ip = "2"
    # Klaim atomik DULU: cegah double-claim bila tombol diklik 2x cepat
    if not record_trial_claim(tid, svc, username):
        await event.edit("✅ **Kamu sudah mengambil trial hari ini.**",
            buttons=[[Button.inline("‹ Panel Utama","up-main")]])
        return
    await event.edit(f"⏳ **Membuat akun trial {label}...**")
    try:
        api_create_account(svc, username, password=password, limit_ip=limit_ip, days=1, trial=True, timeout=30)
    except:
        await event.edit("❌ **Gagal membuat akun trial.**\n\nSilakan coba lagi.",
            buttons=[[Button.inline("‹ Kembali","up-trial")]])
        return
    # Schedule cleanup after 1 hour (dengan fallback bila `at` tidak ada)
    _schedule_trial_kill(svc, username)
    expired_at = (DT.datetime.now() + DT.timedelta(hours=1)).strftime('%Y-%m-%d %H:%M')
    db = get_db()
    db.execute("INSERT INTO user_services (telegram_id,service,username,expired_at) VALUES (?,?,?,?)",
        (tid, svc, username, expired_at))
    db.commit()
    try:
        raw = subprocess.check_output(f'cat /var/www/html/{fname}-{username}.txt', shell=True).decode("utf-8")
        result = f"🎁 **TRIAL {label.upper()}**\n\n```\n{raw.strip()}\n```\n⏳ **Masa Aktif** : 1 Jam\n💾 [Simpan Akun](https://{DOMAIN}:8443/{fname}-{username}.txt)"
    except:
        result = (
            f"🎁 **TRIAL {label.upper()}**\n\n"
            f"👤 **Username** : `{username}`\n"
            f"🌐 **Host** : `{DOMAIN}`\n"
            f"⏳ **Masa Aktif** : 1 Jam\n\n"
            f"💾 [Simpan Akun](https://{DOMAIN}:8443/{fname}-{username}.txt)"
        )
    try:
        await bot.send_message(int(tid), result,
            buttons=[[Button.inline("‹ Panel Utama","up-main")]])
    except:
        await event.edit(result,
            buttons=[[Button.inline("‹ Panel Utama","up-main")]])
    await notify_admin(
        f"🎁 **TRIAL GRATIS**\n\n"
        f"👤 `{tid}`\n"
        f"{emoji} **Layanan** : {label}\n"
        f"🏷️ **Username** : `{username}`\n"
        f"⏳ **Masa Aktif** : 1 Jam"
    )

# ── LAYANAN SAYA ──────────────────────────────────────────────────────
@bot.on(events.CallbackQuery(data=b'up-layanan'))
async def up_layanan(event):
    sender = await event.get_sender()
    svcs = get_user_services(str(sender.id))
    if not svcs:
        await event.edit("📋 **LAYANAN SAYA**\n\n_Belum ada layanan aktif._",
            buttons=[[Button.inline("🛒 Beli","up-beli")],[Button.inline("‹ Back","up-main")]])
        return
    msg = "📋 **LAYANAN SAYA**\n\n"
    btns = []
    for s in svcs:
        e = SVC_EMOJI.get(s['service'],'🔧')
        msg += f"{e} `{s['username']}` — exp: `{s['expired_at']}`\n"
        btns.append([Button.inline(f"{e} {s['username']}", f"up-det-{s['id']}")])
    btns.append([Button.inline("‹ Back","up-main")])
    await event.edit(msg, buttons=btns)

@bot.on(events.CallbackQuery(func=lambda e: e.data.startswith(b'up-det-')))
async def up_detail(event):
    sid = int(event.data.decode().replace('up-det-',''))
    sender = await event.get_sender()
    db = get_db()
    s = db.execute("SELECT * FROM user_services WHERE id=? AND telegram_id=?",
        (sid, str(sender.id))).fetchone()
    if not s:
        await event.answer("Tidak ditemukan.", alert=True)
        return
    svc = s['service']
    uname = s['username']
    emoji = SVC_EMOJI.get(svc,'🔧')
    label = SVC_LABEL.get(svc, svc.upper())
    fname = SVC_FILE.get(svc, svc)
    if svc == 'ssh':
        msg = (
            f"{emoji} **{label}**\n\n"
            f"👤 **Username** : `{uname}`\n"
            f"🌐 **Host** : `{DOMAIN}`\n"
            f"⏳ **Expired** : `{s['expired_at']}`\n\n"
            f"**◇━━━━━━━━━━◇**\n"
            f"OpenSSH → `{DOMAIN}:80@{uname}:****`\n"
            f"SSH WS  → `{DOMAIN}:443@{uname}:****`\n"
            f"UDP     → `{DOMAIN}:1-65535@{uname}:****`\n\n"
            f"💾 [Simpan Akun](https://{DOMAIN}:8443/ssh-{uname}.txt)"
        )
    else:
        msg = (
            f"{emoji} **{label}**\n\n"
            f"👤 **Username** : `{uname}`\n"
            f"🌐 **Host** : `{DOMAIN}`\n"
            f"⏳ **Expired** : `{s['expired_at']}`\n\n"
            f"💾 [Lihat Detail](https://{DOMAIN}:8443/{fname}-{uname}.txt)"
        )
    await event.edit(msg, buttons=[
        [Button.inline("🔄 Minta Renew", f"up-req-{s['id']}"),
         Button.inline("‹ Back","up-layanan")]
    ])

# ── CEK STATUS ────────────────────────────────────────────────────────
@bot.on(events.CallbackQuery(data=b'up-status'))
async def up_status(event):
    sender = await event.get_sender()
    svcs = get_user_services(str(sender.id))
    if not svcs:
        await event.edit("📊 **STATUS**\n\n_Belum ada layanan._",
            buttons=[[Button.inline("‹ Back","up-main")]])
        return
    today = DT.date.today()
    msg = "📊 **STATUS AKUN**\n\n"
    for s in svcs:
        emoji = SVC_EMOJI.get(s['service'],'🔧')
        try:
            exp = DT.date.fromisoformat(s['expired_at'])
            sisa = (exp - today).days
            if sisa > 3:
                st = f"✅ Aktif ({sisa} hari)"
            elif sisa > 0:
                st = f"⚠️ Segera expired ({sisa} hari)"
            else:
                st = "❌ Expired"
        except:
            st = "⚠️ Unknown"
        msg += f"{emoji} `{s['username']}` — {st}\n"
    await event.edit(msg, buttons=[[Button.inline("‹ Back","up-main")]])

# ── MINTA RENEW ───────────────────────────────────────────────────────
@bot.on(events.CallbackQuery(data=b'up-renew'))
async def up_renew_menu(event):
    sender = await event.get_sender()
    svcs = get_user_services(str(sender.id))
    if not svcs:
        await event.edit("🔄 **RENEW**\n\n_Belum ada layanan._",
            buttons=[[Button.inline("‹ Back","up-main")]])
        return
    btns = [[Button.inline(
        f"{SVC_EMOJI.get(s['service'],'🔧')} {s['username']}",
        f"up-req-{s['id']}"
    )] for s in svcs]
    btns.append([Button.inline("‹ Back","up-main")])
    await event.edit("🔄 **MINTA RENEW**\n\nPilih akun:", buttons=btns)

@bot.on(events.CallbackQuery(func=lambda e: e.data.startswith(b'up-req-')))
async def up_renew_req(event):
    sid = int(event.data.decode().replace('up-req-',''))
    sender = await event.get_sender()
    db = get_db()
    s = db.execute("SELECT * FROM user_services WHERE id=? AND telegram_id=?",
        (sid, str(sender.id))).fetchone()
    if not s:
        await event.answer("Tidak ditemukan.", alert=True)
        return
    tg_ref = f"@{sender.username}" if sender.username else f"ID:{sender.id}"
    emoji = SVC_EMOJI.get(s['service'],'🔧')
    label = SVC_LABEL.get(s['service'], s['service'].upper())
    await notify_admin(
        f"🔔 **PERMINTAAN RENEW**\n\n"
        f"👤 {tg_ref} (`{sender.id}`)\n"
        f"{emoji} **Layanan** : {label}\n"
        f"🏷️ **Username** : `{s['username']}`\n"
        f"⏳ **Expired** : `{s['expired_at']}`\n\n"
        f"Segera proses renewal!"
    )
    await event.edit(
        f"✅ **Permintaan renew terkirim!**\n\n"
        f"Admin akan segera memproses `{s['username']}`.",
        buttons=[[Button.inline("‹ Back","up-main")]]
    )

# ── INFO SERVER ───────────────────────────────────────────────────────
@bot.on(events.CallbackQuery(data=b'up-server'))
async def up_server(event):
    try:
        z = requests.get("http://ip-api.com/json/?fields=country,isp", timeout=5).json()
        isp = z.get('isp','N/A')
        country = z.get('country','N/A')
    except:
        isp = country = 'N/A'
    await event.edit(
        f"ℹ️ **INFO SERVER**\n\n"
        f"🌐 **Domain** : `{DOMAIN}`\n"
        f"🏢 **ISP** : {isp}\n"
        f"🌍 **Country** : {country}\n\n"
        f"**◇━━━━━━━━━━◇**\n**── Port ──**\n**◇━━━━━━━━━━◇**\n"
        f"OpenSSH : `22, 80, 443`\n"
        f"Dropbear : `109, 143`\n"
        f"SSL/TLS : `443`\n"
        f"Xray : `443 (TLS), 80 (NTLS)`",
        buttons=[[Button.inline("‹ Back","up-main")]]
    )

# ══════════════════════════════════════════════════════════════════════
# ADMIN COMMANDS
# ══════════════════════════════════════════════════════════════════════

@bot.on(events.NewMessage(pattern=r'/topup'))
async def admin_topup(event):
    sender = await event.get_sender()
    if valid(str(sender.id)) != "true":
        return
    parts = event.raw_text.split()
    if len(parts) != 3:
        await event.respond("**Format:** `/topup [telegram_id] [jumlah]`\n**Contoh:** `/topup 123456789 50000`")
        return
    try:
        tid = parts[1]
        amount = float(parts[2])
    except ValueError:
        await event.respond("❌ Jumlah harus angka.")
        return
    ensure_user_exists(tid)
    add_balance(tid, amount, "Top Up Admin")
    new_bal = get_balance(tid)
    await event.respond(
        f"✅ **Top Up Berhasil**\n\n"
        f"🆔 ID : `{tid}`\n"
        f"➕ Tambah : `{format_rupiah(amount)}`\n"
        f"💰 Saldo : `{format_rupiah(new_bal)}`"
    )
    try:
        await bot.send_message(int(tid),
            f"💰 **Saldo ditambahkan!**\n\n"
            f"➕ `{format_rupiah(amount)}`\n"
            f"💵 Saldo sekarang : `{format_rupiah(new_bal)}`")
    except:
        pass

@bot.on(events.NewMessage(pattern=r'/ceksaldo'))
async def admin_ceksaldo(event):
    sender = await event.get_sender()
    if valid(str(sender.id)) != "true":
        return
    parts = event.raw_text.split()
    if len(parts) != 2:
        await event.respond("**Format:** `/ceksaldo [telegram_id]`")
        return
    tid = parts[1]
    bal = get_balance(tid)
    db = get_db()
    user = db.execute("SELECT tg_username FROM user_balance WHERE telegram_id=?", (tid,)).fetchone()
    uname = user['tg_username'] if user else 'N/A'
    svcs = get_user_services(tid)
    await event.respond(
        f"📊 **Info User**\n\n"
        f"🆔 ID : `{tid}`\n"
        f"👤 Username : @{uname}\n"
        f"💰 Saldo : `{format_rupiah(bal)}`\n"
        f"📦 Layanan : `{len(svcs)}` akun"
    )

@bot.on(events.NewMessage(pattern=r'/setprice'))
async def admin_setprice(event):
    sender = await event.get_sender()
    if valid(str(sender.id)) != "true":
        return
    parts = event.raw_text.split()
    if len(parts) != 4:
        await event.respond(
            "**Format:** `/setprice [service] [durasi] [harga]`\n"
            "**Contoh:** `/setprice ssh 30 20000`\n\n"
            "**Service:** ssh, vmess, vless, trojan, shadowsocks")
        return
    try:
        svc = parts[1].lower()
        dur = int(parts[2])
        price = float(parts[3])
    except ValueError:
        await event.respond("❌ Format salah.")
        return
    if svc not in SVC_LABEL:
        await event.respond("❌ Service tidak valid.")
        return
    db = get_db()
    db.execute("INSERT OR REPLACE INTO service_prices VALUES (?,?,?)", (svc, dur, price))
    db.commit()
    await event.respond(
        f"✅ **Harga diperbarui**\n\n"
        f"🔧 {SVC_LABEL[svc]} — {dur} hari\n"
        f"💵 Harga baru : `{format_rupiah(price)}`"
    )

@bot.on(events.NewMessage(pattern=r'/allusers'))
async def admin_allusers(event):
    sender = await event.get_sender()
    if valid(str(sender.id)) != "true":
        return
    db = get_db()
    users = db.execute(
        "SELECT telegram_id, tg_username, balance FROM user_balance ORDER BY joined_at DESC LIMIT 20"
    ).fetchall()
    if not users:
        await event.respond("📋 Belum ada user terdaftar.")
        return
    msg = "📋 **DAFTAR USER** (20 terakhir)\n\n"
    for u in users:
        uname = f"@{u['tg_username']}" if u['tg_username'] else u['telegram_id']
        msg += f"• {uname} — `{format_rupiah(u['balance'])}`\n"
    await event.respond(msg)

@bot.on(events.NewMessage(pattern=r'/pricelist'))
async def admin_pricelist(event):
    sender = await event.get_sender()
    if valid(str(sender.id)) != "true":
        return
    db = get_db()
    prices = db.execute("SELECT * FROM service_prices ORDER BY service, duration").fetchall()
    msg = "💵 **DAFTAR HARGA**\n\n"
    current_svc = ""
    for p in prices:
        if p['service'] != current_svc:
            current_svc = p['service']
            emoji = SVC_EMOJI.get(current_svc,'🔧')
            label = SVC_LABEL.get(current_svc, current_svc.upper())
            msg += f"\n{emoji} **{label}**\n"
        msg += f"  • {p['duration']} hari : `{format_rupiah(p['price'])}`\n"
    await event.respond(msg)

# ── BALANCE MANAGEMENT (Callback-based) ────────────────────────────────
@bot.on(events.CallbackQuery(data=b'adm-balance'))
async def adm_balance_menu(event):
    sender = await event.get_sender()
    if valid(str(sender.id)) != "true":
        await event.answer("Access Denied", alert=True)
        return
    btns = [
        [Button.inline("💰 Top Up","adm-topup"),
         Button.inline("💵 Cek Saldo","adm-ceksaldo")],
        [Button.inline("💲 Set Harga","adm-setharga"),
         Button.inline("📋 Price List","adm-pricelist")],
        [Button.inline("👥 All Users","adm-allusers")],
        [Button.inline("‹ Back","setting")],
    ]
    await event.edit("**💰 BALANCE MANAGEMENT**\nPilih opsi:", buttons=btns)

@bot.on(events.CallbackQuery(data=b'adm-topup'))
async def adm_topup_cb(event):
    sender = await event.get_sender()
    if valid(str(sender.id)) != "true":
        return
    chat = event.chat_id
    async with bot.conversation(chat) as user_conv:
        await event.respond("**Masukkan ID Telegram user:**")
        user_resp = user_conv.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
        user_resp = (await user_resp).raw_text.strip()
    async with bot.conversation(chat) as amt_conv:
        await event.respond("**Masukkan jumlah top up:**")
        amt_resp = amt_conv.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
        amt_resp = (await amt_resp).raw_text.strip()
    try:
        amount = float(amt_resp)
    except ValueError:
        await event.respond("❌ Jumlah harus angka.")
        return
    ensure_user_exists(user_resp)
    add_balance(user_resp, amount, "Top Up Admin")
    new_bal = get_balance(user_resp)
    await event.respond(
        f"✅ **Top Up Berhasil**\n\n"
        f"🆔 ID : `{user_resp}`\n"
        f"➕ Tambah : `{format_rupiah(amount)}`\n"
        f"💰 Saldo : `{format_rupiah(new_bal)}`"
    )
    try:
        await bot.send_message(int(user_resp),
            f"💰 **Saldo ditambahkan!**\n\n"
            f"➕ `{format_rupiah(amount)}`\n"
            f"💵 Saldo sekarang : `{format_rupiah(new_bal)}`")
    except:
        pass

@bot.on(events.CallbackQuery(data=b'adm-ceksaldo'))
async def adm_ceksaldo_cb(event):
    sender = await event.get_sender()
    if valid(str(sender.id)) != "true":
        return
    chat = event.chat_id
    async with bot.conversation(chat) as conv:
        await event.respond("**Masukkan ID Telegram user:**")
        resp = conv.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
        tid = (await resp).raw_text.strip()
    bal = get_balance(tid)
    db = get_db()
    user = db.execute("SELECT tg_username FROM user_balance WHERE telegram_id=?", (tid,)).fetchone()
    uname = user['tg_username'] if user else 'N/A'
    svcs = get_user_services(tid)
    await event.respond(
        f"📊 **Info User**\n\n"
        f"🆔 ID : `{tid}`\n"
        f"👤 Username : @{uname}\n"
        f"💰 Saldo : `{format_rupiah(bal)}`\n"
        f"📦 Layanan : `{len(svcs)}` akun"
    )

@bot.on(events.CallbackQuery(data=b'adm-pricelist'))
async def adm_pricelist_cb(event):
    sender = await event.get_sender()
    if valid(str(sender.id)) != "true":
        return
    db = get_db()
    prices = db.execute("SELECT * FROM service_prices ORDER BY service, duration").fetchall()
    msg = "💵 **DAFTAR HARGA**\n\n"
    current_svc = ""
    for p in prices:
        if p['service'] != current_svc:
            current_svc = p['service']
            emoji = SVC_EMOJI.get(current_svc,'🔧')
            label = SVC_LABEL.get(current_svc, current_svc.upper())
            msg += f"\n{emoji} **{label}**\n"
        msg += f"  • {p['duration']} hari : `{format_rupiah(p['price'])}`\n"
    msg += "\n_Admin: /setprice untuk mengubah harga_"
    await event.edit(msg, buttons=[[Button.inline("‹ Back","adm-balance")]])

@bot.on(events.CallbackQuery(data=b'adm-allusers'))
async def adm_allusers_cb(event):
    sender = await event.get_sender()
    if valid(str(sender.id)) != "true":
        return
    db = get_db()
    users = db.execute(
        "SELECT telegram_id, tg_username, balance FROM user_balance ORDER BY joined_at DESC LIMIT 20"
    ).fetchall()
    if not users:
        await event.edit("📋 Belum ada user terdaftar.",
            buttons=[[Button.inline("‹ Back","adm-balance")]])
        return
    msg = "📋 **DAFTAR USER** (20 terakhir)\n\n"
    for u in users:
        uname = f"@{u['tg_username']}" if u['tg_username'] else u['telegram_id']
        msg += f"• {uname} — `{format_rupiah(u['balance'])}`\n"
    await event.edit(msg, buttons=[[Button.inline("‹ Back","adm-balance")]])

@bot.on(events.CallbackQuery(data=b'adm-setharga'))
async def adm_setharga_cb(event):
    sender = await event.get_sender()
    if valid(str(sender.id)) != "true":
        return
    chat = event.chat_id
    async with bot.conversation(chat) as svc_conv:
        await event.respond(
            "**Masukkan service, durasi, dan harga**\n"
            "Format: `service durasi harga`\n"
            "Contoh: `ssh 30 20000`\n\n"
            "Service: ssh, vmess, vless, trojan, shadowsocks")
        resp = svc_conv.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
        parts = (await resp).raw_text.strip().split()
    if len(parts) != 3:
        await event.respond("❌ Format salah. Gunakan: `service durasi harga`")
        return
    try:
        svc = parts[0].lower()
        dur = int(parts[1])
        price = float(parts[2])
    except ValueError:
        await event.respond("❌ Format salah. Pastikan durasi dan harga angka.")
        return
    if svc not in SVC_LABEL:
        await event.respond("❌ Service tidak valid. Pilih: ssh, vmess, vless, trojan, shadowsocks")
        return
    db = get_db()
    db.execute("INSERT OR REPLACE INTO service_prices VALUES (?,?,?)", (svc, dur, price))
    db.commit()
    await event.respond(
        f"✅ **Harga diperbarui**\n\n"
        f"🔧 {SVC_LABEL[svc]} — {dur} hari\n"
        f"💵 Harga baru : `{format_rupiah(price)}`"
    )
