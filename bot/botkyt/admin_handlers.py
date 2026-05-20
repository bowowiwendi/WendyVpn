"""Admin handlers for bot management"""
from telegram import Update
from telegram.ext import ContextTypes
import database
import keyboards
import formatter
from decorators import registered_user, not_banned, admin_only, superadmin_only


# ==================== ADMIN PANEL ====================

@admin_only
async def admin_panel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin panel"""
    query = update.callback_query
    await query.answer()
    
    stats = await database.get_stats()
    user = context.user_data['db_user']
    text = formatter.admin_panel_text(stats)
    kb = keyboards.admin_menu_keyboard(user['role'])
    
    await query.edit_message_text(text, reply_markup=kb, parse_mode="HTML")


# ==================== TOP-UP USER ====================

@admin_only
async def admin_topup_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start top-up user flow"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        """
╔══════════════════════════════╗
   💰 <b>TOP-UP SALDO USER</b> 💰
╚══════════════════════════════╝

<i>Kirim ID Telegram user yang ingin di top-up:</i>
<i>(Contoh: 123456789)</i>
""",
        reply_markup=keyboards.back_keyboard("menu_admin"),
        parse_mode="HTML"
    )
    context.user_data['waiting_for'] = 'admin_topup_userid'


async def admin_topup_userid_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user ID input for top-up"""
    if context.user_data.get('waiting_for') != 'admin_topup_userid':
        return
    
    try:
        target_id = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ ID tidak valid. Kirim angka saja.")
        return
    
    target_user = await database.get_user(target_id)
    if not target_user:
        await update.message.reply_text("❌ User tidak ditemukan.")
        return
    
    context.user_data['topup_target'] = target_id
    context.user_data['waiting_for'] = 'admin_topup_amount'
    
    await update.message.reply_text(
        f"""
👤 User: <b>{target_user['full_name'] or target_user['username'] or target_id}</b>
💰 Saldo saat ini: <b>{formatter.format_currency(target_user['balance'])}</b>

<i>Kirim nominal top-up (angka saja):</i>
<i>(Contoh: 50000)</i>
""",
        parse_mode="HTML"
    )


async def admin_topup_amount_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle amount input for top-up"""
    if context.user_data.get('waiting_for') != 'admin_topup_amount':
        return
    
    try:
        amount = int(update.message.text.strip().replace(".", "").replace(",", ""))
    except ValueError:
        await update.message.reply_text("❌ Nominal tidak valid. Kirim angka saja.")
        return
    
    if amount <= 0:
        await update.message.reply_text("❌ Nominal harus lebih dari 0.")
        return
    
    target_id = context.user_data['topup_target']
    admin_id = update.effective_user.id
    
    # Add balance
    await database.update_user_balance(target_id, amount)
    
    # Record transaction
    await database.add_transaction(
        user_id=target_id,
        tx_type="topup",
        amount=amount,
        description=f"Top-up manual oleh admin",
        admin_id=admin_id
    )
    
    target_user = await database.get_user(target_id)
    
    await update.message.reply_text(
        f"""
✅ <b>TOP-UP BERHASIL!</b>

👤 User: <b>{target_user['full_name'] or target_user['username'] or target_id}</b>
💰 Nominal: <b>{formatter.format_currency(amount)}</b>
💳 Saldo baru: <b>{formatter.format_currency(target_user['balance'])}</b>

Ketik /start untuk kembali ke menu.
""",
        parse_mode="HTML"
    )
    
    # Notify user
    try:
        await context.bot.send_message(
            chat_id=target_id,
            text=f"""
💰 <b>SALDO DITAMBAHKAN!</b>

Nominal: <b>{formatter.format_currency(amount)}</b>
Saldo baru: <b>{formatter.format_currency(target_user['balance'])}</b>

<i>Top-up oleh admin.</i>
""",
            parse_mode="HTML"
        )
    except Exception:
        pass
    
    context.user_data['waiting_for'] = None


# ==================== VOUCHER MANAGEMENT ====================

@admin_only
async def admin_voucher_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start create voucher flow"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        """
╔══════════════════════════════╗
   🎫 <b>BUAT VOUCHER</b> 🎫
╚══════════════════════════════╝

<i>Kirim nominal voucher (angka saja):</i>
<i>(Contoh: 10000)</i>

<i>Atau kirim format: nominal jumlah</i>
<i>(Contoh: 10000 5 → buat 5 voucher @Rp10.000)</i>
""",
        reply_markup=keyboards.back_keyboard("menu_admin"),
        parse_mode="HTML"
    )
    context.user_data['waiting_for'] = 'admin_voucher_amount'


async def admin_voucher_amount_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voucher creation"""
    if context.user_data.get('waiting_for') != 'admin_voucher_amount':
        return
    
    import secrets
    
    parts = update.message.text.strip().split()
    
    try:
        amount = int(parts[0].replace(".", "").replace(",", ""))
        count = int(parts[1]) if len(parts) > 1 else 1
    except (ValueError, IndexError):
        await update.message.reply_text("❌ Format tidak valid. Contoh: 10000 atau 10000 5")
        return
    
    if amount <= 0 or count <= 0 or count > 50:
        await update.message.reply_text("❌ Nominal harus > 0 dan jumlah max 50.")
        return
    
    admin_id = update.effective_user.id
    vouchers = []
    
    for _ in range(count):
        code = f"WVP-{secrets.token_hex(4).upper()}"
        await database.create_voucher(code, amount, admin_id)
        vouchers.append(code)
    
    voucher_list = "\n".join([f"<code>{v}</code>" for v in vouchers])
    
    await update.message.reply_text(
        f"""
✅ <b>VOUCHER BERHASIL DIBUAT!</b>

💲 Nominal: <b>{formatter.format_currency(amount)}</b>
📝 Jumlah: <b>{count}</b>

🎫 <b>Kode Voucher:</b>
{voucher_list}

Ketik /start untuk kembali ke menu.
""",
        parse_mode="HTML"
    )
    
    context.user_data['waiting_for'] = None


# ==================== PRICING MANAGEMENT ====================

@admin_only
async def admin_pricing_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show pricing management"""
    query = update.callback_query
    await query.answer()
    
    pricing = await database.get_pricing()
    
    text = """
╔══════════════════════════════╗
   💲 <b>KELOLA HARGA</b> 💲
╚══════════════════════════════╝

"""
    if pricing:
        current_protocol = ""
        for p in pricing:
            if p['protocol'] != current_protocol:
                current_protocol = p['protocol']
                text += f"\n<b>📡 {current_protocol.upper()}</b>\n"
            text += f"  • {p['duration_days']} hari = {formatter.format_currency(p['price'])} ({p['ip_limit']} IP)\n"
    else:
        text += "<i>Belum ada harga yang diatur.</i>\n"
    
    text += """
\n<i>Untuk set harga, kirim format:</i>
<code>harga [protokol] [hari] [harga] [limit_ip]</code>
<i>Contoh: harga vmess 30 10000 2</i>
"""
    
    await query.edit_message_text(
        text,
        reply_markup=keyboards.back_keyboard("menu_admin"),
        parse_mode="HTML"
    )
    context.user_data['waiting_for'] = 'admin_pricing'


async def admin_pricing_input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle pricing input"""
    if context.user_data.get('waiting_for') != 'admin_pricing':
        return
    
    text = update.message.text.strip().lower()
    if not text.startswith("harga"):
        return
    
    parts = text.split()
    if len(parts) < 4:
        await update.message.reply_text(
            "❌ Format: <code>harga [protokol] [hari] [harga] [limit_ip]</code>\n"
            "Contoh: <code>harga vmess 30 10000 2</code>",
            parse_mode="HTML"
        )
        return
    
    try:
        protocol = parts[1]
        days = int(parts[2])
        price = int(parts[3])
        ip_limit = int(parts[4]) if len(parts) > 4 else 2
    except (ValueError, IndexError):
        await update.message.reply_text("❌ Format tidak valid.")
        return
    
    valid_protocols = ['ssh', 'vmess', 'vless', 'trojan', 'shadowsocks']
    if protocol not in valid_protocols:
        await update.message.reply_text(f"❌ Protokol tidak valid. Pilih: {', '.join(valid_protocols)}")
        return
    
    await database.set_pricing(protocol, days, price, ip_limit)
    
    await update.message.reply_text(
        f"""
✅ <b>HARGA BERHASIL DIATUR!</b>

📡 Protokol: <b>{protocol.upper()}</b>
⏱ Durasi: <b>{days} hari</b>
💲 Harga: <b>{formatter.format_currency(price)}</b>
🔗 Limit IP: <b>{ip_limit}</b>

Ketik /start untuk kembali ke menu.
""",
        parse_mode="HTML"
    )


# ==================== SERVER MANAGEMENT ====================

@admin_only
async def admin_servers_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show server management"""
    query = update.callback_query
    await query.answer()
    
    servers = await database.get_servers(active_only=False)
    
    text = """
╔══════════════════════════════╗
   🖥️ <b>KELOLA SERVER</b> 🖥️
╚══════════════════════════════╝

"""
    if servers:
        for s in servers:
            status = "🟢" if s['is_active'] else "🔴"
            text += f"│ {status} <b>{s['name']}</b>\n"
            text += f"│    Host: <code>{s['host']}</code>\n"
            text += f"│    Domain: <code>{s['domain']}</code>\n\n"
    else:
        text += "<i>Belum ada server.</i>\n"
    
    text += """
\n<i>Untuk tambah server, kirim format:</i>
<code>addserver [nama] [host/ip] [domain] [ssh_port] [ssh_pass]</code>
<i>Contoh: addserver SG1 1.2.3.4 sg1.domain.com 22 password123</i>
"""
    
    await query.edit_message_text(
        text,
        reply_markup=keyboards.back_keyboard("menu_admin"),
        parse_mode="HTML"
    )
    context.user_data['waiting_for'] = 'admin_server'


async def admin_server_input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle server management input"""
    if context.user_data.get('waiting_for') != 'admin_server':
        return
    
    text = update.message.text.strip()
    
    if text.lower().startswith("addserver"):
        parts = text.split()
        if len(parts) < 5:
            await update.message.reply_text(
                "❌ Format: <code>addserver [nama] [host] [domain] [ssh_port] [ssh_pass]</code>",
                parse_mode="HTML"
            )
            return
        
        try:
            name = parts[1]
            host = parts[2]
            domain = parts[3]
            ssh_port = int(parts[4]) if len(parts) > 4 else 22
            ssh_password = parts[5] if len(parts) > 5 else None
        except (ValueError, IndexError):
            await update.message.reply_text("❌ Format tidak valid.")
            return
        
        await database.add_server(name, host, domain, ssh_port, "root", ssh_password)
        
        await update.message.reply_text(
            f"""
✅ <b>SERVER BERHASIL DITAMBAHKAN!</b>

🖥️ Nama: <b>{name}</b>
📡 Host: <code>{host}</code>
🌐 Domain: <code>{domain}</code>
🔌 SSH Port: <b>{ssh_port}</b>

Ketik /start untuk kembali ke menu.
""",
            parse_mode="HTML"
        )
    
    elif text.lower().startswith("delserver"):
        parts = text.split()
        if len(parts) < 2:
            await update.message.reply_text("❌ Format: <code>delserver [id]</code>", parse_mode="HTML")
            return
        
        try:
            server_id = int(parts[1])
        except ValueError:
            await update.message.reply_text("❌ ID tidak valid.")
            return
        
        await database.delete_server(server_id)
        await update.message.reply_text("✅ Server berhasil dinonaktifkan.")


# ==================== STATISTICS ====================

@admin_only
async def admin_stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show detailed statistics"""
    query = update.callback_query
    await query.answer()
    
    stats = await database.get_stats()
    
    text = f"""
╔══════════════════════════════╗
   📊 <b>STATISTIK LENGKAP</b> 📊
╚══════════════════════════════╝

<b>👥 USER</b>
┌─────────────────────────
│ Total User    : <b>{stats['total_users']}</b>
│ Total Admin   : <b>{stats['total_admins']}</b>
└─────────────────────────

<b>💰 KEUANGAN</b>
┌─────────────────────────
│ Total Saldo   : <b>{formatter.format_currency(stats['total_balance'])}</b>
│ Total Revenue : <b>{formatter.format_currency(stats['total_revenue'])}</b>
└─────────────────────────

<b>📡 LAYANAN</b>
┌─────────────────────────
│ Akun Aktif    : <b>{stats['active_accounts']}</b>
│ Server Aktif  : <b>{stats['active_servers']}</b>
└─────────────────────────
"""
    
    await query.edit_message_text(
        text,
        reply_markup=keyboards.back_keyboard("menu_admin"),
        parse_mode="HTML"
    )


# ==================== BROADCAST ====================

@admin_only
async def admin_broadcast_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start broadcast flow"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        """
╔══════════════════════════════╗
   📢 <b>BROADCAST</b> 📢
╚══════════════════════════════╝

<i>Kirim pesan yang ingin di-broadcast ke semua user:</i>
""",
        reply_markup=keyboards.back_keyboard("menu_admin"),
        parse_mode="HTML"
    )
    context.user_data['waiting_for'] = 'admin_broadcast'


async def admin_broadcast_input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle broadcast message"""
    if context.user_data.get('waiting_for') != 'admin_broadcast':
        return
    
    message = update.message.text.strip()
    users = await database.get_all_users()
    
    success = 0
    failed = 0
    
    for user in users:
        try:
            await context.bot.send_message(
                chat_id=user['telegram_id'],
                text=f"📢 <b>BROADCAST</b>\n\n{message}",
                parse_mode="HTML"
            )
            success += 1
        except Exception:
            failed += 1
    
    await update.message.reply_text(
        f"""
✅ <b>BROADCAST SELESAI!</b>

📤 Terkirim: <b>{success}</b>
❌ Gagal: <b>{failed}</b>

Ketik /start untuk kembali ke menu.
""",
        parse_mode="HTML"
    )
    
    context.user_data['waiting_for'] = None


# ==================== MANAGE ADMINS ====================

@superadmin_only
async def admin_manage_admins_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manage admin roles"""
    query = update.callback_query
    await query.answer()
    
    admins = await database.get_all_users(role="admin")
    
    text = """
╔══════════════════════════════╗
   👑 <b>KELOLA ADMIN</b> 👑
╚══════════════════════════════╝

"""
    if admins:
        for a in admins:
            text += f"│ 🛡️ {a['full_name'] or a['username'] or a['telegram_id']}\n"
            text += f"│    ID: <code>{a['telegram_id']}</code>\n\n"
    else:
        text += "<i>Belum ada admin.</i>\n"
    
    text += """
\n<i>Perintah:</i>
<code>addadmin [telegram_id]</code> - Tambah admin
<code>deladmin [telegram_id]</code> - Hapus admin
"""
    
    await query.edit_message_text(
        text,
        reply_markup=keyboards.back_keyboard("menu_admin"),
        parse_mode="HTML"
    )
    context.user_data['waiting_for'] = 'admin_manage'


async def admin_manage_input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin management input"""
    if context.user_data.get('waiting_for') != 'admin_manage':
        return
    
    text = update.message.text.strip().lower()
    
    if text.startswith("addadmin"):
        parts = text.split()
        if len(parts) < 2:
            await update.message.reply_text("❌ Format: <code>addadmin [telegram_id]</code>", parse_mode="HTML")
            return
        
        try:
            target_id = int(parts[1])
        except ValueError:
            await update.message.reply_text("❌ ID tidak valid.")
            return
        
        target = await database.get_user(target_id)
        if not target:
            await update.message.reply_text("❌ User tidak ditemukan. User harus /start bot dulu.")
            return
        
        await database.set_user_role(target_id, "admin")
        await update.message.reply_text(
            f"✅ <b>{target['full_name'] or target_id}</b> sekarang menjadi Admin!",
            parse_mode="HTML"
        )
    
    elif text.startswith("deladmin"):
        parts = text.split()
        if len(parts) < 2:
            await update.message.reply_text("❌ Format: <code>deladmin [telegram_id]</code>", parse_mode="HTML")
            return
        
        try:
            target_id = int(parts[1])
        except ValueError:
            await update.message.reply_text("❌ ID tidak valid.")
            return
        
        await database.set_user_role(target_id, "user")
        await update.message.reply_text(f"✅ Admin dengan ID {target_id} telah diturunkan ke User.")


# ==================== USER MANAGEMENT ====================

@admin_only
async def admin_users_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user management"""
    query = update.callback_query
    await query.answer()
    
    users = await database.get_all_users()
    total = len(users)
    
    text = f"""
╔══════════════════════════════╗
   👥 <b>KELOLA USER</b> 👥
╚══════════════════════════════╝

📊 Total User: <b>{total}</b>

"""
    # Show last 10 users
    for u in users[:10]:
        role_emoji = {"superadmin": "👑", "admin": "🛡️", "user": "👤"}
        e = role_emoji.get(u['role'], '👤')
        name = u['full_name'] or u['username'] or str(u['telegram_id'])
        text += f"│ {e} {name} | {formatter.format_currency(u['balance'])}\n"
    
    if total > 10:
        text += f"\n<i>...dan {total - 10} user lainnya</i>\n"
    
    text += """
\n<i>Perintah:</i>
<code>banuser [telegram_id]</code> - Ban user
<code>unbanuser [telegram_id]</code> - Unban user
<code>cekuser [telegram_id]</code> - Cek detail user
"""
    
    await query.edit_message_text(
        text,
        reply_markup=keyboards.back_keyboard("menu_admin"),
        parse_mode="HTML"
    )
    context.user_data['waiting_for'] = 'admin_users'


async def admin_users_input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user management input"""
    if context.user_data.get('waiting_for') != 'admin_users':
        return
    
    text = update.message.text.strip().lower()
    
    if text.startswith("banuser"):
        parts = text.split()
        if len(parts) < 2:
            return
        try:
            target_id = int(parts[1])
            await database.ban_user(target_id, True)
            await update.message.reply_text(f"✅ User {target_id} telah di-ban.")
        except ValueError:
            await update.message.reply_text("❌ ID tidak valid.")
    
    elif text.startswith("unbanuser"):
        parts = text.split()
        if len(parts) < 2:
            return
        try:
            target_id = int(parts[1])
            await database.ban_user(target_id, False)
            await update.message.reply_text(f"✅ User {target_id} telah di-unban.")
        except ValueError:
            await update.message.reply_text("❌ ID tidak valid.")
    
    elif text.startswith("cekuser"):
        parts = text.split()
        if len(parts) < 2:
            return
        try:
            target_id = int(parts[1])
            target = await database.get_user(target_id)
            if target:
                accounts = await database.get_user_vpn_accounts(target_id)
                await update.message.reply_text(
                    f"""
👤 <b>DETAIL USER</b>

┌─────────────────────────
│ 🆔 ID: <code>{target['telegram_id']}</code>
│ 👤 Nama: <b>{target['full_name'] or '-'}</b>
│ 📛 Username: @{target['username'] or '-'}
│ 🛡️ Role: <b>{target['role']}</b>
│ 💰 Saldo: <b>{formatter.format_currency(target['balance'])}</b>
│ 💸 Total Spent: <b>{formatter.format_currency(target['total_spent'])}</b>
│ 📡 Akun Aktif: <b>{len(accounts)}</b>
│ 🚫 Banned: <b>{'Ya' if target['is_banned'] else 'Tidak'}</b>
│ 📅 Bergabung: <b>{target['created_at'][:10]}</b>
└─────────────────────────
""",
                    parse_mode="HTML"
                )
            else:
                await update.message.reply_text("❌ User tidak ditemukan.")
        except ValueError:
            await update.message.reply_text("❌ ID tidak valid.")


# ==================== LIST ACCOUNTS ====================

@admin_only
async def admin_accounts_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show all active VPN accounts"""
    query = update.callback_query
    await query.answer()
    
    import aiosqlite
    from config import DB_PATH
    
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT va.*, s.name as server_name, u.full_name, u.username as tg_username
               FROM vpn_accounts va
               LEFT JOIN servers s ON va.server_id = s.id
               LEFT JOIN users u ON va.user_id = u.telegram_id
               WHERE va.status = 'active'
               ORDER BY va.created_at DESC
               LIMIT 20"""
        )
        accounts = await cursor.fetchall()
    
    text = """
╔══════════════════════════════╗
   📋 <b>DAFTAR AKUN AKTIF</b> 📋
╚══════════════════════════════╝

"""
    if accounts:
        for acc in accounts:
            emoji = {"ssh": "🔵", "vmess": "🟢", "vless": "🟡", "trojan": "🔴", "shadowsocks": "🟣"}
            e = emoji.get(acc['protocol'], "📡")
            owner = acc['full_name'] or acc['tg_username'] or str(acc['user_id'])
            text += f"│ {e} <b>{acc['username']}</b> ({acc['protocol']})\n"
            text += f"│    Owner: {owner} | Exp: {acc['expired_date']}\n\n"
    else:
        text += "<i>Tidak ada akun aktif.</i>\n"
    
    await query.edit_message_text(
        text,
        reply_markup=keyboards.back_keyboard("menu_admin"),
        parse_mode="HTML"
    )
