from kyt import *
from kyt.modules.server_manager import exec_cmd, get_active, get_server

#detail
@bot.on(events.CallbackQuery(data=b'd-vless'))
async def l_vless(event):
    async def l_vless_(event):
        cmd = 'cat /etc/xray/config.json | grep "^#&" | cut -d " " -f 2-3 | sort | uniq | nl'.strip()
        x = exec_cmd(cmd, tid)
        z = x.decode("utf-8")
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
            user = clean_username((await user_event).raw_text)
            if not user:
                await event.respond("**Username tidak valid.** Gunakan huruf/angka/_/- (maks 32 karakter).")
                return
            if not config_user_exists('/etc/xray/config.json', user):
                await event.respond("**Username tidak ditemukan. Silakan masukkan username yang benar.**", buttons=[
[Button.inline("🔄 Ulangi","d-vless")],
[Button.inline("❌ Batal","vless")]])
                return
            z = read_detail_file('vless', user)
            if z:
                await event.respond(f"""
**◇━━━━━━━━━━◇**
    ** ⟨🔸 Vless Account🔸⟩**
**◇━━━━━━━━━━◇**
```
{z}
```
""",buttons=[[Button.inline("‹ Kembali","vless")]])
            else:
                await event.respond("**Filed**: User tidak ditemukan", buttons=[[Button.inline("‹ Kembali","vless")]])
    chat = event.chat_id
    sender = await event.get_sender()
    tid = str(sender.id)
    a = valid(str(sender.id))
    if a == "true":
        await l_vless_(event)
    else:
        await event.answer("Akses Ditolak",alert=True)

#LOCK vless
@bot.on(events.CallbackQuery(data=b'lock-vless'))
async def lock_vless(event):
    chat = event.chat_id
    sender = await event.get_sender()
    tid = str(sender.id)
    a = valid(str(sender.id))
    if a != "true":
        await event.answer("Akses Ditolak",alert=True)
        return
    async def lock_vless_(event):
        cmd = 'cat /etc/xray/config.json | grep "^#&" | cut -d " " -f 2-3 | sort | uniq | nl'.strip()
        x = exec_cmd(cmd, tid)
        z = x.decode("utf-8")
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
            user = clean_username((await user).raw_text)
            if not user:
                await event.respond("**Username tidak valid.** Gunakan huruf/angka/_/- (maks 32 karakter).")
                return
            if not config_user_exists('/etc/xray/config.json', user):
                await event.respond("**Username tidak ditemukan.**", buttons=[
                    [Button.inline("🔄 Ulangi", "lock-vless")],
                    [Button.inline("❌ Batal", "vless")]])
                return
            cmd = f'printf "%s\n" "{user}" | lock-vl'
        try:
            a = exec_cmd(cmd, tid).decode("utf-8")
        except subprocess.CalledProcessError as e:
            await event.respond("❌ Gagal: " + str(getattr(e, "stderr", e) or "command failed"), buttons=[[Button.inline("‹ Kembali","vless")]])
        else:
            await event.respond(f" **Successfully Lock**", buttons=[[Button.inline("‹ Kembali","vless")]])
    await lock_vless_(event)

#UNLOCK vless
@bot.on(events.CallbackQuery(data=b'unlock-vless'))
async def unlock_vless(event):
    chat = event.chat_id
    sender = await event.get_sender()
    tid = str(sender.id)
    a = valid(str(sender.id))
    if a != "true":
        await event.answer("Akses Ditolak",alert=True)
        return
    async def unlock_vless_(event):
        cmd = 'cat /etc/xray/.lock.db | grep "^#&" | cut -d " " -f 2-3 | sort | uniq | nl'.strip()
        x = exec_cmd(cmd, tid)
        z = x.decode("utf-8")
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
            user = clean_username((await user).raw_text)
            if not user:
                await event.respond("**Username tidak valid.** Gunakan huruf/angka/_/- (maks 32 karakter).")
                return
            if not config_user_exists('/etc/xray/config.json', user):
                await event.respond("**Username tidak ditemukan.**", buttons=[
                    [Button.inline("🔄 Ulangi", "unlock-vless")],
                    [Button.inline("❌ Batal", "vless")]])
                return
            cmd = f'printf "%s\n" "{user}" | unlock-vl'
        try:
            a = exec_cmd(cmd, tid).decode("utf-8")
        except subprocess.CalledProcessError as e:
            await event.respond("❌ Gagal: " + str(getattr(e, "stderr", e) or "command failed"), buttons=[[Button.inline("‹ Kembali","vless")]])
        else:
            await event.respond(f" **Successfully Unlock**", buttons=[[Button.inline("‹ Kembali","vless")]])
    await unlock_vless_(event)

_admin_create_state = {}

async def _admin_ask_username(event, chat, state):
    state['step'] = 'username'
    await bot.send_message(chat, "🔡 **Username:**\n\nKetik username, atau klik 🔀 Acak untuk nama acak.",
        buttons=[[Button.inline("🔀 Acak", "adm-rand-vless-uname")], [Button.inline("❌ Batal", "vless")]])

async def _admin_ask_limit_ip(event, chat, state):
    state['step'] = 'limit_ip'
    await bot.send_message(chat, "🌐 **Limit IP:**\n\nMasukkan angka limit IP.",
        buttons=[[Button.inline("❌ Batal", "vless")]])

async def _admin_ask_quota(event, chat, state):
    state['step'] = 'quota'
    await bot.send_message(chat, "📦 **Quota (GB):**\n\nMasukkan jumlah quota.",
        buttons=[[Button.inline("❌ Batal", "vless")]])

async def _admin_ask_expiry(event, chat, state):
    state['step'] = 'expiry'
    await bot.send_message(chat, "⏳ **Masaaktif (hari):**\n\nMasukkan jumlah hari.",
        buttons=[[Button.inline("❌ Batal", "vless")]])

async def _admin_finish_create(event, chat, state):
    if chat in _admin_create_state:
        del _admin_create_state[chat]
    user = state['username']
    limit_ip = state['limit_ip']
    quota = state['quota']
    exp = state['expiry']
    random_user = state.get('random_user', False)
    svr_label = state.get('svr_label', '')
    tid = state['_tid']
    done = False
    last_err = None
    for attempt in range(5 if random_user else 1):
        uname = ("user" + str(random.randint(1000, 9999)) if random_user else user)
        try:
            a = api_create_account('vless', uname if 'uname' in locals() else user, limit_ip=limit_ip, quota=quota if 'quota' in locals() else pw, days=exp, bug=bug if 'bug' in locals() else '')
            user = uname
            done = True
            break
        except Exception as e:
            last_err = e
            if random_user:
                continue
            break
    if not done:
        if last_err and "exist" in str(last_err).lower():
            await bot.send_message(chat, f"❌ **Username `{user}` sudah dipakai.** Coba username lain.",
                buttons=[[Button.inline("‹ Kembali","vless")]])
        else:
            await bot.send_message(chat, f"**Gagal membuat akun.** `{last_err or 'Coba lagi.'}`",
                buttons=[[Button.inline("‹ Kembali","vless")]])
        return
    today = DT.date.today()
    later = today + DT.timedelta(days=int(exp))
    x = extract_vpn_links(a, "vless")
    if len(x) < 3:
        await bot.send_message(chat, "❌ **Gagal memproses link akun.**", buttons=[[Button.inline("‹ Kembali","vless")]])
        return
    uuid = extract_link_field(x[0], r"vless://(.*?)@")
    msg = f"""
🔷 **VLESS ACCOUNT**

👤 **Username** : `{user}`
🔑 **UUID** : `{uuid}`
🌐 **Host** : `{DOMAIN}`
📱 **Limit IP** : `{limit_ip}`
📦 **Quota** : `{quota}` GB
⏳ **Expired** : `{later}`

**◇━━━━━━━━━━◇**
🔗 **TLS** : `{x[0]}`
🔗 **gRPC** : `{x[2].replace(" ","")}`
💾 [OpenClash](https://{DOMAIN}:8443/vless-{user}.txt)
{svr_label}
"""
    await bot.send_message(chat, msg, buttons=[[Button.inline("‹ Kembali","vless")]])

@bot.on(events.CallbackQuery(data=b'create-vless'))
async def create_vless(event):
    chat = event.chat_id
    sender = await event.get_sender()
    tid = str(sender.id)
    a = valid(str(sender.id))
    if a != "true":
        await event.answer("Akses Ditolak",alert=True)
        return
    svr_label = ""
    svr_id = get_active(tid)
    if svr_id is not None:
        s = get_server(svr_id)
        if s:
            svr_label = f"\n**📍 Remote:** `{s['name']}`"
    state = {
        'svc': 'vless', 'step': None,
        'username': None, 'limit_ip': None,
        'quota': None, 'expiry': None,
        'random_user': False, 'svr_label': svr_label,
        '_chat': chat, '_tid': tid, '_sender_id': sender.id,
    }
    _admin_create_state[chat] = state
    await _admin_ask_username(event, chat, state)

@bot.on(events.NewMessage(incoming=True))
async def _admin_handle_create_input(event):
    chat = event.chat_id
    if chat not in _admin_create_state:
        return
    state = _admin_create_state[chat]
    sender = await event.get_sender()
    if sender.id != state.get('_sender_id'):
        return
    text = event.raw_text.strip().replace(" ", "")
    step = state.get('step')
    
    if step == 'username':
        if not text or text.lower() == 'random':
            state['username'] = "user" + str(random.randint(1000, 9999))
            state['random_user'] = True
            await event.respond("✅ Username acak: `" + state['username'] + "`")
        else:
            cu = clean_username(text)
            if not cu:
                await event.respond("❌ Username tidak valid. Gunakan huruf/angka/_/- (maks 32 karakter).")
                return
            state['username'] = cu
            state['random_user'] = False
        await _admin_ask_limit_ip(event, chat, state)
    elif step == 'limit_ip':
        if not text.isdigit():
            await event.respond("❌ Limit IP harus angka.", buttons=[[Button.inline("🔄 Ulangi", "create-vless")]])
            return
        state['limit_ip'] = text
        await _admin_ask_quota(event, chat, state)
    elif step == 'quota':
        if not text.isdigit():
            await event.respond("❌ Quota harus angka.", buttons=[[Button.inline("🔄 Ulangi", "create-vless")]])
            return
        state['quota'] = text
        await _admin_ask_expiry(event, chat, state)
    elif step == 'expiry':
        if not text.isdigit():
            await event.respond("❌ Masaaktif harus angka.", buttons=[[Button.inline("🔄 Ulangi", "create-vless")]])
            return
        state['expiry'] = text
        await _admin_finish_create(event, chat, state)

@bot.on(events.CallbackQuery(data=b'adm-rand-vless-uname'))
async def _admin_rand_vless_uname(event):
    chat = event.chat_id
    state = _admin_create_state.get(chat)
    if not state or state.get('step') != 'username':
        return
    state['username'] = "user" + str(random.randint(1000, 9999))
    state['random_user'] = True
    await event.edit("✅ Username acak: `" + state['username'] + "`")
    await _admin_ask_limit_ip(event, chat, state)

@bot.on(events.CallbackQuery(data=b'auto-vless'))
async def auto_vless(event):
    chat = event.chat_id
    sender = await event.get_sender()
    tid = str(sender.id)
    a = valid(str(sender.id))
    if a != "true":
        await event.answer("Akses Ditolak",alert=True)
        return
    svr_label = ""
    svr_id = get_active(tid)
    if svr_id is not None:
        s = get_server(svr_id)
        if s:
            svr_label = f"\n**📍 Remote:** `{s['name']}`"
    async def auto_vless_(event):
        nonlocal svr_label
        async with bot.conversation(chat) as limit_ip:
            await event.respond("🌐 **Limit IP:**")
            limit_ip = limit_ip.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
            limit_ip = (await limit_ip).raw_text
            if not limit_ip.isdigit():
                await event.respond("🌐 **Limit IP harus berupa angka.**", buttons=[
[Button.inline("🔄 Create Ulang","create-vless")],
[Button.inline("❌ Batal","vless")]])
                return
        async with bot.conversation(chat) as pw:
            await event.respond("📦 **Quota:**")
            pw = pw.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
            pw = (await pw).raw_text
            if not pw.isdigit():
                await event.respond("📦 **Quota harus berupa angka.**", buttons=[
[Button.inline("🔄 Create Ulang","create-vless")],
[Button.inline("❌ Batal","vless")]])
                return
        async with bot.conversation(chat) as exp:
            await event.respond("⏳ **Masaaktif:**")
            exp = exp.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
            exp = (await exp).raw_text
            if not exp.isdigit():
                await event.respond("⏳ **Masaaktif harus berupa angka.**", buttons=[
[Button.inline("🔄 Create Ulang","create-vless")],
[Button.inline("❌ Batal","vless")]])
                return
        bug = ""
        user = "VlessPrem"+str(random.randint(100,1000))
        try:
            a = api_create_account('vless', uname if 'uname' in locals() else user, limit_ip=limit_ip, quota=quota if 'quota' in locals() else pw, days=exp, bug=bug if 'bug' in locals() else '')
        except Exception as e:
            msg_err = "**User Already Exist**" if "exist" in str(e).lower() else f"❌ **Gagal membuat akun:** `{e}`"
            await event.respond(msg_err)
        else:
            inline=[[Button.inline("‹ Kembali","vless")]]
            today = DT.date.today()
            later = today + DT.timedelta(days=int(exp))
            x = extract_vpn_links(a, "vless")
            if len(x) < 3:
                await event.respond("❌ **Gagal memproses link akun.**", buttons=inline)
                return
            uuid = extract_link_field(x[0], r"vless://(.*?)@")
            msg = f"""
🔷 **VLESS ACCOUNT**

👤 **Username** : `{user}`
🔑 **UUID** : `{uuid}`
🌐 **Host** : `{DOMAIN}`
📱 **Limit IP** : `{limit_ip}`
📦 **Quota** : `{pw}` GB
⏳ **Expired** : `{later}`

**◇━━━━━━━━━━◇**
🔗 **TLS** : `{x[0]}`
🔗 **gRPC** : `{x[2].replace(" ","")}`
💾 [OpenClash](https://{DOMAIN}:8443/vless-{user}.txt)
{svr_label}
"""
            await event.respond(msg,buttons=inline)
    await auto_vless_(event)

@bot.on(events.CallbackQuery(data=b'cek-vless'))
async def cek_vless(event):
    async def cek_vless_(event):
        cmd = 'bot-cek-vless'.strip()
        x = exec_cmd(cmd, tid)
        z = x.decode("utf-8")
        await event.respond(f"""
**◇━━━━━━━━━━◇**
    ** ⟨🔸 Vless Logged🔸⟩**
**◇━━━━━━━━━━◇**
```                      
{z}
```
**Shows Logged In Users Vless**
» 🤖 @WendiVpn
""",buttons=[[Button.inline("‹ Kembali","vless")]])
    sender = await event.get_sender()
    tid = str(sender.id)
    a = valid(str(sender.id))
    if a == "true":
        await cek_vless_(event)
    else:
        await event.answer("Access Denied",alert=True)

@bot.on(events.CallbackQuery(data=b'delete-vless'))
async def delete_vless(event):
    chat = event.chat_id
    sender = await event.get_sender()
    tid = str(sender.id)
    a = valid(str(sender.id))
    if a != "true":
        await event.answer("Akses Ditolak",alert=True)
        return
    async def delete_vless_(event):
        cmd = 'cat /etc/xray/config.json | grep "^#&" | cut -d " " -f 2-3 | sort | uniq | nl'.strip()
        x = exec_cmd(cmd, tid)
        z = x.decode("utf-8")
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
            user = clean_username((await user).raw_text)
            if not user:
                await event.respond("**Username tidak valid.** Gunakan huruf/angka/_/- (maks 32 karakter).")
                return
            if not config_user_exists('/etc/xray/config.json', user):
                await event.respond("**Username tidak ditemukan.**", buttons=[
                    [Button.inline("🔄 Ulangi", "delete-vless")],
                    [Button.inline("❌ Batal", "vless")]])
                return
        try:
            a = api_delete_account('vless', user)
        except subprocess.CalledProcessError as e:
            await event.respond("❌ Gagal: " + str(getattr(e, "stderr", e) or "command failed"), buttons=[[Button.inline("‹ Kembali","vless")]])
        else:
            await event.respond(f" **Successfully Delet**", buttons=[[Button.inline("‹ Kembali","vless")]])
    await delete_vless_(event)

@bot.on(events.CallbackQuery(data=b'trial-vless'))
async def trial_vless(event):
    chat = event.chat_id
    sender = await event.get_sender()
    tid = str(sender.id)
    a = valid(str(sender.id))
    if a != "true":
        await event.answer("Akses Ditolak",alert=True)
        return
    svr_label = ""
    svr_id = get_active(tid)
    if svr_id is not None:
        s = get_server(svr_id)
        if s:
            svr_label = f"\n**📍 Remote:** `{s['name']}`"
    async def trial_vless_(event):
        nonlocal svr_label
        async with bot.conversation(chat) as exp:
            await event.respond("**Choose Expiry Minutes**",buttons=[
[Button.inline(" 10 Menit ","10"),
Button.inline(" 15 Menit ","15")],
[Button.inline(" 30 Menit ","30"),
Button.inline(" 60 Menit ","60")]])
            exp = exp.wait_event(events.CallbackQuery)
            exp = (await exp).data.decode("ascii")
        if exp not in ("10", "15", "30", "60"):
            await event.respond("**Pilihan menit tidak valid.**")
            return
        trial_user = f'trial{random.randint(1000,9999)}'
        try:
            # Trial dalam MENIT: buat akun days=1 lalu jadwalkan hapus setelah exp menit
            a = api_create_account('vless', trial_user, days=1, trial=True)
        except Exception as e:
            msg_err = "**User Already Exist**" if "exist" in str(e).lower() else f"❌ **Gagal membuat trial:** `{e}`"
            await event.respond(msg_err)
        else:
            schedule_trial_kill('vless', trial_user, minutes=int(exp))
            inline=[[Button.inline("‹ Kembali","vless")]]
            x = extract_vpn_links(a, "vless")
            if len(x) < 3:
                await event.respond("❌ **Gagal memproses link akun trial.**", buttons=inline)
                return
            remarks = extract_link_field(x[0], r"#(.*)")
            uuid = extract_link_field(x[0], r"vless://(.*?)@")
            msg = f"""
🔷 **VLESS ACCOUNT**

👤 **Username** : `{remarks}`
🔑 **UUID** : `{uuid}`
🌐 **Host** : `{DOMAIN}`
📱 **Limit IP** : `-`
📦 **Quota** : `Unlimited`
⏳ **Expired** : `{exp} Minutes`

**◇━━━━━━━━━━◇**
🔗 **TLS** : `{x[0]}`
🔗 **gRPC** : `{x[2].replace(" ","")}`
💾 [OpenClash](https://{DOMAIN}:8443/vless-{remarks}.txt)
{svr_label}
"""
            await event.respond(msg,buttons=inline)
    await trial_vless_(event)

@bot.on(events.CallbackQuery(data=b'bot-member-vl'))
async def bot_member_vl(event):
    async def bot_member_vl_(event):
        cmd = 'cat /etc/xray/config.json | grep "^#&" | cut -d " " -f 2-3 | sort | uniq | nl'.strip()
        x = exec_cmd(cmd, tid)
        z = x.decode("utf-8")
        await event.respond(f"""
**◇━━━━━━━━━━◇**
    ** ⟨🔸 Vless Account🔸⟩**
**◇━━━━━━━━━━◇**
```
{z}
```
**Menampilkan Member Vless**
» 🤖 @WendiVpn
""",buttons=[[Button.inline("‹ Kembali","vless")]])
    sender = await event.get_sender()
    tid = str(sender.id)
    a = valid(str(sender.id))
    if a == "true":
        await bot_member_vl_(event)
    else:
        await event.answer("Akses Ditolak",alert=True)

@bot.on(events.CallbackQuery(data=b'renew-vl'))
async def renew_vl(event):
    chat = event.chat_id
    sender = await event.get_sender()
    tid = str(sender.id)
    a = valid(str(sender.id))
    if a != "true":
        await event.answer("Akses Ditolak",alert=True)
        return
    async def renew_vl_(event):
        cmd = 'cat /etc/xray/config.json | grep "^#&" | cut -d " " -f 2-3 | sort | uniq | nl'.strip()
        x = exec_cmd(cmd, tid)
        z = x.decode("utf-8")
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
            user = clean_username((await user).raw_text)
            if not user:
                await event.respond("**Username tidak valid.** Gunakan huruf/angka/_/- (maks 32 karakter).")
                return
            if not config_user_exists('/etc/xray/config.json', user):
                await event.respond("**Username tidak ditemukan.**", buttons=[
                    [Button.inline("🔄 Ulangi", "renew-vl")],
                    [Button.inline("❌ Batal", "vless")]])
                return
        async with bot.conversation(chat) as exp:
            await event.respond(' **Ubah Masaaktif:**')
            exp = exp.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
            exp = (await exp).raw_text
            if not exp.isdigit():
                await event.respond(" **Masaaktif harus berupa angka.**", buttons=[
[Button.inline("🔄 Renew Ulang","renew-ws")],
[Button.inline("❌ Batal","vless")]])
                return
        async with bot.conversation(chat) as quota:
            await event.respond(' **Limit Quota:**')
            quota = quota.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
            quota = (await quota).raw_text
            if not quota.isdigit():
                await event.respond(" **Limit Quota harus berupa angka.**", buttons=[
[Button.inline("🔄 Renew Ulang","renew-ws")],
[Button.inline("❌ Batal","vless")]])
                return
        async with bot.conversation(chat) as ip:
            await event.respond(' **Limit Ip:**')
            ip = ip.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
            ip = (await ip).raw_text
            if not ip.isdigit():
                await event.respond(" **Limit Ip harus berupa angka.**", buttons=[
[Button.inline("🔄 Renew Ulang","renew-ws")],
[Button.inline("❌ Batal","vless")]])
                return
        try:
            a = api_renew_account('vless', user, days=exp, quota=quota, limit_ip=ip)
        except Exception as e:
            await event.respond(f"❌ **Gagal renew** `{user}`:\n`{e}`",buttons=[[Button.inline("‹ Kembali","vless")]])
        else:
            await event.respond(f"**Successfully Renew** `{user}`",buttons=[[Button.inline("‹ Kembali","vless")]])
    await renew_vl_(event)


@bot.on(events.CallbackQuery(data=b'vless'))
async def vless(event):
    async def vless_(event):
        inline = [
[Button.inline("☣️ Trial","trial-vless"),
Button.inline("➕ Create","create-vless")],
[Button.inline("♻️ Renew","renew-vl"),
Button.inline("👤 Member","bot-member-vl")],
[Button.inline("✅ Check","cek-vless"),
Button.inline("❌ Delete","delete-vless")],
[Button.inline("🔒 Lock","lock-vless"),
Button.inline("🔐 Unlock","unlock-vless")],
[Button.inline("📝 Detail","d-vless")],
[Button.inline("‹ Kembali","menu")]]
        z = requests.get(f"http://ip-api.com/json/?fields=query,country,city,timezone,isp").json()
        vl = f' cat /etc/vless/.vless.db | grep "###" | wc -l'
        vls = exec_cmd(vl, tid).decode("ascii")
        username = sender.username
        user_id = sender.id
        msg = f"""
🔷 **VLESS MANAGER**

🌐 **Host** : `{DOMAIN}`
🖥️ **IP** : `{z['query']}`
📍 **{z['country']}**, {z['city']}
🏢 **{z['isp']}**
📊 **Total** : `{vls.strip()}` akun

🆔 **ID** : `{user_id}` 👤 **@{username}**
"""
        await event.edit(msg,buttons=inline)
    sender = await event.get_sender()
    tid = str(sender.id)
    a = valid(str(sender.id))
    if a == "true":
        await vless_(event)
    else:
        await event.answer("Access Denied",alert=True)
