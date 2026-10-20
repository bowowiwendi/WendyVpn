from kyt import *
from kyt.modules.server_manager import exec_cmd, get_active, get_server

#detail
@bot.on(events.CallbackQuery(data=b'd-ssh'))
async def l_ssh(event):
    async def l_ssh_(event):
        cmd = 'bot-member-ssh'.strip()
        try:
            z = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
        except subprocess.CalledProcessError:
            z = ""
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
            user = clean_username((await user_event).raw_text)
            if not user:
                await event.respond("**Username tidak valid.** Gunakan huruf/angka/_/- (maks 32 karakter).")
                return
            cmd_check = f'grep -E "^{user}:" /etc/passwd'
            if subprocess.call(cmd_check, shell=True) != 0:
                await event.respond("**Username tidak ditemukan. Silakan masukkan username yang benar.**", buttons=[
[Button.inline("🔄 Ulangi","d-ssh")],
[Button.inline("‹ Kembali","ssh")]])
                return
            cmd = f'cat /var/www/html/ssh-{user}.txt'.strip()
            try:
                z = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
            except subprocess.CalledProcessError:
                z = ""
            if z:
                await event.respond(f"""
**◇━━━━━━━━━━◇**
    ** ⟨🔸 SSH Account🔸⟩**
**◇━━━━━━━━━━◇**
```
{z}
```
""",buttons=[[Button.inline("‹ Kembali","ssh")]])
            else:
                await event.respond("**Filed**: User tidak ditemukan", buttons=[[Button.inline("‹ Kembali","ssh")]])
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
    chat = event.chat_id
    sender = await event.get_sender()
    tid = str(sender.id)
    a = valid(str(sender.id))
    if a != "true":
        await event.answer("Akses Ditolak",alert=True)
        return
    async def user_unlock_(event):
        cmd = 'bot-member-ssh'.strip()
        x = exec_cmd(cmd, tid)
        z = x.decode("utf-8")
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
            user = clean_username((await user_event).raw_text)
            if not user:
                await event.respond("**Username tidak valid.** Gunakan huruf/angka/_/- (maks 32 karakter).")
                return
            cmd_check = f'grep -E "^{user}:" /etc/passwd'
            if subprocess.call(cmd_check, shell=True) != 0:
                await event.respond("**Username tidak ditemukan.**", buttons=[
                    [Button.inline("🔄 Ulangi", "user-unlock")],
                    [Button.inline("❌ Batal", "ssh")]])
                return
            cmd = f'printf "%s\n" "{user}" | user-unlock.sh'
        try:
            a = exec_cmd(cmd, tid).decode("utf-8")
        except subprocess.CalledProcessError as e:
            await event.respond("❌ Gagal: " + str(getattr(e, "stderr", e) or "command failed"), buttons=[[Button.inline("‹ Kembali","ssh")]])
        else:
            await event.respond(f" **Successfully Unlock**", buttons=[[Button.inline("‹ Kembali","ssh")]])
    await user_unlock_(event)

#LOCKSSH
@bot.on(events.CallbackQuery(data=b'user-lock'))
async def user_lock(event):
    chat = event.chat_id
    sender = await event.get_sender()
    tid = str(sender.id)
    a = valid(str(sender.id))
    if a != "true":
        await event.answer("Akses Ditolak",alert=True)
        return
    async def user_lock_(event):
        cmd = 'bot-member-ssh'.strip()
        x = exec_cmd(cmd, tid)
        z = x.decode("utf-8")
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
            user = clean_username((await user_event).raw_text)
            if not user:
                await event.respond("**Username tidak valid.** Gunakan huruf/angka/_/- (maks 32 karakter).")
                return
            cmd_check = f'grep -E "^{user}:" /etc/passwd'
            if subprocess.call(cmd_check, shell=True) != 0:
                await event.respond("**Username tidak ditemukan.**", buttons=[
                    [Button.inline("🔄 Ulangi", "user-lock")],
                    [Button.inline("❌ Batal", "ssh")]])
                return
            cmd = f'printf "%s\n" "{user}" | user-lock.sh'
        try:
            a = exec_cmd(cmd, tid).decode("utf-8")
        except subprocess.CalledProcessError as e:
            await event.respond("❌ Gagal: " + str(getattr(e, "stderr", e) or "command failed"), buttons=[[Button.inline("‹ Kembali","ssh")]])
        else:
            await event.respond(f" **Successfully Lock**", buttons=[[Button.inline("‹ Kembali","ssh")]])
    await user_lock_(event)

#DELETESSH
@bot.on(events.CallbackQuery(data=b'delete-ssh'))
async def delete_ssh(event):
    chat = event.chat_id
    sender = await event.get_sender()
    tid = str(sender.id)
    a = valid(str(sender.id))
    if a != "true":
        await event.answer("Akses Ditolak",alert=True)
        return
    async def delete_ssh_(event):
        cmd = 'bot-member-ssh'.strip()
        x = exec_cmd(cmd, tid)
        z = x.decode("utf-8")
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
            user = clean_username((await user_event).raw_text)
            if not user:
                await event.respond("**Username tidak valid.** Gunakan huruf/angka/_/- (maks 32 karakter).")
                return
            cmd_check = f'grep -E "^{user}:" /etc/passwd'
            if subprocess.call(cmd_check, shell=True) != 0:
                await event.respond("**Username tidak ditemukan.**", buttons=[
                    [Button.inline("🔄 Ulangi", "delete-ssh")],
                    [Button.inline("❌ Batal", "ssh")]])
                return
        try:
            a = api_delete_account('ssh', user)
        except subprocess.CalledProcessError as e:
            await event.respond("❌ Gagal: " + str(getattr(e, "stderr", e) or "command failed"), buttons=[[Button.inline("‹ Kembali","ssh")]])
        else:
            await event.respond(f" **Successfully Delet**", buttons=[[Button.inline("‹ Kembali","ssh")]])
    await delete_ssh_(event)

_admin_create_state = {}

async def _admin_ask_username(event, chat, state):
    state['step'] = 'username'
    await bot.send_message(chat, "🔡 **Username:**\n\nKetik username, atau klik 🔀 Acak untuk nama acak.",
        buttons=[[Button.inline("🔀 Acak", "adm-rand-ssh-uname")], [Button.inline("❌ Batal", "ssh")]])

async def _admin_ask_password(event, chat, state):
    state['step'] = 'password'
    await bot.send_message(chat, "🔑 **Password:**\n\nKetik password, atau klik 🔀 Acak untuk password acak.",
        buttons=[[Button.inline("🔀 Acak", "adm-rand-ssh-pass")], [Button.inline("❌ Batal", "ssh")]])

async def _admin_ask_limit_ip(event, chat, state):
    state['step'] = 'limit_ip'
    await bot.send_message(chat, "🌐 **Limit IP:**\n\nMasukkan angka limit IP.",
        buttons=[[Button.inline("❌ Batal", "ssh")]])

async def _admin_ask_expiry(event, chat, state):
    state['step'] = 'expiry'
    await bot.send_message(chat, "⏳ **Masaaktif (hari):**\n\nMasukkan jumlah hari.",
        buttons=[[Button.inline("❌ Batal", "ssh")]])

async def _admin_finish_create(event, chat, state):
    if chat in _admin_create_state:
        del _admin_create_state[chat]
    user = state['username']
    pw = state['password']
    limit_ip = state['limit_ip']
    exp = state['expiry']
    random_user = state.get('random_user', False)
    svr_label = state.get('svr_label', '')
    tid = state['_tid']
    done = False
    for attempt in range(5 if random_user else 1):
        uname = ("user" + str(random.randint(1000, 9999)) if random_user else user)
        try:
            api_create_account('ssh', uname if 'uname' in locals() else user, password=pw, limit_ip=limit_ip, days=exp, bug=bug if 'bug' in locals() else '')
            user = uname
            done = True
            break
        except:
            if random_user:
                continue
            break
    if not done:
        await bot.send_message(chat, "**Gagal membuat akun. Coba lagi.**", buttons=[[Button.inline("‹ Kembali","ssh")]])
        return
    today = DT.date.today()
    later = today + DT.timedelta(days=int(exp))
    msg = f"""
🔐 **SSH OVPN ACCOUNT**

👤 **Username** : `{user.strip()}`
🔑 **Password** : `{pw.strip()}`
🌐 **Host** : `{DOMAIN}`
📱 **Limit IP** : `{limit_ip.strip()}`
⏳ **Expired** : `{later}`

**◇━━━━━━━━━━◇**
OpenSSH → `{DOMAIN}:80@{user.strip()}:{pw.strip()}`
SSH WS  → `{DOMAIN}:443@{user.strip()}:{pw.strip()}`
UDP     → `{DOMAIN}:1-65535@{user.strip()}:{pw.strip()}`

**── OpenVPN ──**
[WS SSL](https://{DOMAIN}:8443/ws-ssl.ovpn) · [SSL](https://{DOMAIN}:8443/ssl.ovpn) · [TCP](https://{DOMAIN}:8443/tcp.ovpn) · [UDP](https://{DOMAIN}:8443/udp.ovpn)

💾 [Simpan Akun](https://{DOMAIN}:8443/ssh-{user.strip()}.txt)
{svr_label}
"""
    qdata = f"{DOMAIN}:80@{user.strip()}:{pw.strip()}"
    await bot.send_message(chat, msg, buttons=[[Button.inline("‹ Kembali","ssh")]])

@bot.on(events.CallbackQuery(data=b'create-ssh'))
async def create_ssh(event):
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
        'svc': 'ssh', 'step': None,
        'username': None, 'password': None,
        'limit_ip': None, 'expiry': None,
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
            state['username'] = text
            state['random_user'] = False
        await _admin_ask_password(event, chat, state)
    elif step == 'password':
        if not text or text.lower() == 'random':
            state['password'] = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=8))
            await event.respond("✅ Password acak: `" + state['password'] + "`")
        else:
            state['password'] = text
        await _admin_ask_limit_ip(event, chat, state)
    elif step == 'limit_ip':
        if not text.isdigit():
            await event.respond("❌ Limit IP harus angka.", buttons=[[Button.inline("🔄 Ulangi", "create-ssh")]])
            return
        state['limit_ip'] = text
        await _admin_ask_expiry(event, chat, state)
    elif step == 'expiry':
        if not text.isdigit():
            await event.respond("❌ Masaaktif harus angka.", buttons=[[Button.inline("🔄 Ulangi", "create-ssh")]])
            return
        state['expiry'] = text
        await _admin_finish_create(event, chat, state)

@bot.on(events.CallbackQuery(data=b'adm-rand-ssh-uname'))
async def _admin_rand_ssh_uname(event):
    chat = event.chat_id
    state = _admin_create_state.get(chat)
    if not state or state.get('step') != 'username':
        return
    state['username'] = "user" + str(random.randint(1000, 9999))
    state['random_user'] = True
    await event.edit("✅ Username acak: `" + state['username'] + "`")
    await _admin_ask_password(event, chat, state)

@bot.on(events.CallbackQuery(data=b'adm-rand-ssh-pass'))
async def _admin_rand_ssh_pass(event):
    chat = event.chat_id
    state = _admin_create_state.get(chat)
    if not state or state.get('step') != 'password':
        return
    state['password'] = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=8))
    await event.edit("✅ Password acak: `" + state['password'] + "`")
    await _admin_ask_limit_ip(event, chat, state)

@bot.on(events.CallbackQuery(data=b'show-ssh'))
async def show_ssh(event):
    async def show_ssh_(event):
        cmd = 'bot-member-ssh'.strip()
        try:
            z = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, universal_newlines=True)
        except subprocess.CalledProcessError:
            z = ""
        await event.respond(f"""
**◇━━━━━━━━━━◇**
    ** ⟨🔸 SSH Account🔸⟩**
**◇━━━━━━━━━━◇**
```
{z}
```
**Show All SSH User**
» 🤖 @WendiVpn
""",buttons=[[Button.inline("‹ Kembali","ssh")]])
    sender = await event.get_sender()
    a = valid(str(sender.id))
    if a == "true":
        await show_ssh_(event)
    else:
        await event.answer("Access Denied",alert=True)


@bot.on(events.CallbackQuery(data=b'auto-ssh'))
async def auto_ssh(event):
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
    async def auto_ssh_(event):
        nonlocal svr_label
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
[Button.inline("❌ Batal","ssh")]])
                return
        async with bot.conversation(chat) as exp:
            await event.respond("⏳ **Masaaktif:**")
            exp = exp.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
            exp = (await exp).raw_text
            if not exp.isdigit():
                await event.respond("⏳ **Masaaktif harus berupa angka.**", buttons=[
[Button.inline("🔄 Auto Ulang","auto-ssh")],
[Button.inline("❌ Batal","ssh")]])
                return
        bug = ""
        user = "Premium"+str(random.randint(100,1000))
        try:
            api_create_account('ssh', uname if 'uname' in locals() else user, password=pw, limit_ip=limit_ip, days=exp, bug=bug if 'bug' in locals() else '')
        except:
            await event.respond("**User Already Exist**",buttons=[[Button.inline("‹ Kembali","menu")]])
        else:
            inline=[[Button.inline("‹ Kembali","ssh")]]
            today = DT.date.today()
            later = today + DT.timedelta(days=int(exp))
            msg = f"""
🔐 **SSH OVPN ACCOUNT**

👤 **Username** : `{user.strip()}`
🔑 **Password** : `{pw.strip()}`
🌐 **Host** : `{DOMAIN}`
📱 **Limit IP** : `{limit_ip.strip()}`
⏳ **Expired** : `{later}`

**◇━━━━━━━━━━◇**
OpenSSH → `{DOMAIN}:80@{user.strip()}:{pw.strip()}`
SSH WS  → `{DOMAIN}:443@{user.strip()}:{pw.strip()}`
UDP     → `{DOMAIN}:1-65535@{user.strip()}:{pw.strip()}`

**── OpenVPN ──**
[WS SSL](https://{DOMAIN}:8443/ws-ssl.ovpn) · [SSL](https://{DOMAIN}:8443/ssl.ovpn) · [TCP](https://{DOMAIN}:8443/tcp.ovpn) · [UDP](https://{DOMAIN}:8443/udp.ovpn)

💾 [Simpan Akun](https://{DOMAIN}:8443/ssh-{user.strip()}.txt)
{svr_label}
"""
            await event.respond(msg,buttons=inline)
    await auto_ssh_(event)

@bot.on(events.CallbackQuery(data=b'trial-ssh'))
async def trial_ssh(event):
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
    async def trial_ssh_(event):
        nonlocal svr_label
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
        try:
            api_create_account('ssh', user, password=pw, limit_ip=limit_ip, days=exp, trial=True)
        except:
            await event.respond("**User Already Exist**",buttons=[[Button.inline("‹ Kembali","ssh")]])
        else:
            inline=[[Button.inline("‹ Kembali","ssh")]]
            today = DT.date.today()
            later = today + DT.timedelta(days=int(exp))
            msg = f"""
🔐 **SSH OVPN ACCOUNT**

👤 **Username** : `{user.strip()}`
🔑 **Password** : `{pw.strip()}`
🌐 **Host** : `{DOMAIN}`
📱 **Limit IP** : `{limit_ip.strip()}`
⏳ **Expired** : `{exp} Minutes`

**◇━━━━━━━━━━◇**
OpenSSH → `{DOMAIN}:80@{user.strip()}:{pw.strip()}`
SSH WS  → `{DOMAIN}:443@{user.strip()}:{pw.strip()}`
UDP     → `{DOMAIN}:1-65535@{user.strip()}:{pw.strip()}`

**── OpenVPN ──**
[WS SSL](https://{DOMAIN}:8443/ws-ssl.ovpn) · [SSL](https://{DOMAIN}:8443/ssl.ovpn) · [TCP](https://{DOMAIN}:8443/tcp.ovpn) · [UDP](https://{DOMAIN}:8443/udp.ovpn)

💾 [Simpan Akun](https://{DOMAIN}:8443/ssh-{user.strip()}.txt)
{svr_label}
"""
            await event.respond(msg,buttons=inline)
    await trial_ssh_(event)
        
        
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
        footer = "\n» 🤖 @WendiVpn"
        back_btn = [[Button.inline("‹ Kembali","ssh")]]
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
    chat = event.chat_id
    sender = await event.get_sender()
    tid = str(sender.id)
    a = valid(str(sender.id))
    if a != "true":
        await event.answer("Akses Ditolak",alert=True)
        return
    async def renew_ssh_(event):
        cmd = 'bot-member-ssh'.strip()
        x = exec_cmd(cmd, tid)
        z = x.decode("utf-8")
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
            user = clean_username((await user_event).raw_text)
            if not user:
                await event.respond("**Username tidak valid.** Gunakan huruf/angka/_/- (maks 32 karakter).")
                return
            cmd_check = f'grep -E "^{user}:" /etc/passwd'
            if subprocess.call(cmd_check, shell=True) != 0:
                await event.respond("**Username tidak ditemukan.**", buttons=[
                    [Button.inline("🔄 Ulangi", "renew-ssh")],
                    [Button.inline("❌ Batal", "ssh")]])
                return
        async with bot.conversation(chat) as conv_exp:
            await event.respond(' **Ubah Masaaktif:**')
            exp_event = conv_exp.wait_event(events.NewMessage(incoming=True, from_users=sender.id))
            exp = (await exp_event).raw_text
            if not exp.isdigit():
                await event.respond(" **Masaaktif harus berupa angka.**", buttons=[
[Button.inline("🔄 Renew Ulang","renew-ssh")],
[Button.inline("‹ Kembali","ssh")]])
                return
        try:
            a = api_renew_account('ssh', user, days=exp)
        except Exception as e:
            logging.exception("renew ssh gagal untuk %s", user)
            await event.respond(f"**Gagal renew** `{user}`:\n`{e}`",buttons=[[Button.inline("‹ Kembali","ssh")]])
        else:
            await event.respond(f"**Successfully Renew** `{user}`",buttons=[[Button.inline("‹ Kembali","ssh")]])
    await renew_ssh_(event)

@bot.on(events.CallbackQuery(data=b'ssh'))
async def ssh(event):
    async def ssh_(event):
        inline = [
[Button.inline("☣️ Trial","trial-ssh"),
Button.inline("➕ Create","create-ssh")],
[Button.inline("❌ Delete","delete-ssh"),
Button.inline("✅ Check","login-ssh")],
[Button.inline("👤 Member","show-ssh"),
Button.inline("♻️ Renew","renew-ssh")],
[Button.inline("🔒 Lock","user-lock"),
Button.inline("🔐 Unlock","user-unlock")],
[Button.inline("📝 Detail","d-ssh")],
[Button.inline("‹ Kembali","menu")]]
        z = requests.get(f"http://ip-api.com/json/?fields=query,country,city,timezone,isp").json()
        sh = f'cat /etc/ssh/.ssh.db | grep "###" | wc -l'
        ssh_count = subprocess.check_output(sh, shell=True).decode("ascii").strip()
        username = sender.username
        user_id = sender.id
        msg = f"""
🔐 **SSH OVPN MANAGER**

🌐 **Host** : `{DOMAIN}`
🖥️ **IP** : `{z['query']}`
📍 **{z['country']}**, {z['city']}
🏢 **{z['isp']}**
📊 **Total** : `{ssh_count}` akun

🆔 **ID** : `{user_id}` 👤 **@{username}**
"""
        await event.edit(msg,buttons=inline)
    sender = await event.get_sender()
    a = valid(str(sender.id))
    if a == "true":
        await ssh_(event)
    else:
        await event.answer("Access Denied",alert=True)
