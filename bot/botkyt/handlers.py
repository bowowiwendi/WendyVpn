"""Main handlers for bot - start, menu navigation, and core callbacks"""
from telegram import Update
from telegram.ext import ContextTypes
import database
import keyboards
import formatter
from decorators import registered_user, not_banned, admin_only, superadmin_only


# ==================== START & MAIN MENU ====================

@registered_user
@not_banned
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = context.user_data['db_user']
    text = formatter.main_menu_text(user)
    kb = keyboards.main_menu_keyboard(user['role'])
    
    if update.message:
        await update.message.reply_text(text, reply_markup=kb, parse_mode="HTML")
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=kb, parse_mode="HTML")


@registered_user
@not_banned
async def back_main_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle back to main menu"""
    query = update.callback_query
    await query.answer()
    
    user = context.user_data['db_user']
    text = formatter.main_menu_text(user)
    kb = keyboards.main_menu_keyboard(user['role'])
    
    await query.edit_message_text(text, reply_markup=kb, parse_mode="HTML")


# ==================== PURCHASE FLOW ====================

@registered_user
@not_banned
async def purchase_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show purchase protocol selection"""
    query = update.callback_query
    await query.answer()
    
    text = formatter.purchase_menu_text()
    kb = keyboards.protocol_keyboard()
    
    await query.edit_message_text(text, reply_markup=kb, parse_mode="HTML")


@registered_user
@not_banned
async def select_protocol_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle protocol selection - show available servers"""
    query = update.callback_query
    await query.answer()
    
    protocol = query.data.replace("buy_", "")
    context.user_data['buy_protocol'] = protocol
    
    servers = await database.get_servers(active_only=True)
    
    if not servers:
        await query.edit_message_text(
            "❌ <b>Tidak ada server tersedia saat ini.</b>\n\nHubungi admin untuk informasi.",
            reply_markup=keyboards.back_keyboard("menu_purchase"),
            parse_mode="HTML"
        )
        return
    
    text = formatter.server_select_text(protocol)
    kb = keyboards.server_select_keyboard(servers, protocol)
    
    await query.edit_message_text(text, reply_markup=kb, parse_mode="HTML")


@registered_user
@not_banned
async def select_server_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle server selection - show available durations"""
    query = update.callback_query
    await query.answer()
    
    # Parse: server_{protocol}_{server_id}
    parts = query.data.split("_")
    protocol = parts[1]
    server_id = int(parts[2])
    
    context.user_data['buy_protocol'] = protocol
    context.user_data['buy_server_id'] = server_id
    
    server = await database.get_server(server_id)
    pricing = await database.get_pricing(protocol=protocol, server_id=server_id)
    
    if not pricing:
        await query.edit_message_text(
            "❌ <b>Belum ada harga untuk protokol ini.</b>\n\nHubungi admin.",
            reply_markup=keyboards.back_keyboard("menu_purchase"),
            parse_mode="HTML"
        )
        return
    
    text = formatter.duration_select_text(protocol, server['name'])
    kb = keyboards.duration_keyboard(pricing, protocol, server_id)
    
    await query.edit_message_text(text, reply_markup=kb, parse_mode="HTML")


@registered_user
@not_banned
async def select_duration_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle duration selection - show confirmation"""
    query = update.callback_query
    await query.answer()
    
    # Parse: dur_{protocol}_{server_id}_{price_id}
    parts = query.data.split("_")
    protocol = parts[1]
    server_id = int(parts[2])
    price_id = int(parts[3])
    
    context.user_data['buy_price_id'] = price_id
    
    # Get pricing details
    import aiosqlite
    from config import DB_PATH
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM pricing WHERE id = ?", (price_id,))
        price_info = await cursor.fetchone()
    
    server = await database.get_server(server_id)
    user = context.user_data['db_user']
    
    text = formatter.confirm_purchase_text(
        protocol=protocol,
        server_name=server['name'],
        duration=price_info['duration_days'],
        price=price_info['price'],
        ip_limit=price_info['ip_limit'],
        quota_gb=price_info['quota_gb'],
        balance=user['balance']
    )
    
    if user['balance'] >= price_info['price']:
        kb = keyboards.confirm_purchase_keyboard(price_id)
    else:
        kb = keyboards.back_keyboard("menu_deposit")
    
    await query.edit_message_text(text, reply_markup=kb, parse_mode="HTML")


@registered_user
@not_banned
async def confirm_purchase_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle purchase confirmation - create VPN account"""
    query = update.callback_query
    await query.answer("⏳ Memproses pembelian...")
    
    # Parse: confirm_buy_{price_id}
    price_id = int(query.data.replace("confirm_buy_", ""))
    
    import aiosqlite
    from config import DB_PATH
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM pricing WHERE id = ?", (price_id,))
        price_info = await cursor.fetchone()
    
    user = context.user_data['db_user']
    protocol = price_info['protocol']
    server_id = price_info['server_id'] or context.user_data.get('buy_server_id')
    
    # Check balance again
    fresh_user = await database.get_user(user['telegram_id'])
    if fresh_user['balance'] < price_info['price']:
        await query.edit_message_text(
            "❌ <b>Saldo tidak cukup!</b>\n\nSilakan deposit terlebih dahulu.",
            reply_markup=keyboards.back_keyboard("menu_deposit"),
            parse_mode="HTML"
        )
        return
    
    # Get server info
    server = await database.get_server(server_id)
    if not server:
        await query.edit_message_text(
            "❌ <b>Server tidak ditemukan.</b>",
            reply_markup=keyboards.back_keyboard("menu_purchase"),
            parse_mode="HTML"
        )
        return
    
    # Create VPN account
    from vpn_manager import VPNManager, generate_username, generate_uuid
    
    vpn = VPNManager(
        host=server['host'],
        port=server['ssh_port'],
        username=server['ssh_user'],
        password=server['ssh_password']
    )
    
    username = generate_username()
    uuid = generate_uuid()
    days = price_info['duration_days']
    ip_limit = price_info['ip_limit']
    
    try:
        if protocol == "ssh":
            import secrets
            password = secrets.token_hex(4)
            result = await vpn.create_ssh(username, password, days, ip_limit)
            uuid = password
        elif protocol == "vmess":
            result = await vpn.create_vmess(username, uuid, days, ip_limit)
        elif protocol == "vless":
            result = await vpn.create_vless(username, uuid, days, ip_limit)
        elif protocol == "trojan":
            result = await vpn.create_trojan(username, uuid, days, ip_limit)
        elif protocol == "shadowsocks":
            import secrets
            password = secrets.token_hex(8)
            result = await vpn.create_shadowsocks(username, password, days, ip_limit)
            uuid = password
        else:
            await query.edit_message_text("❌ Protokol tidak valid.", parse_mode="HTML")
            return
        
        if not result.get('success'):
            await query.edit_message_text(
                "❌ <b>Gagal membuat akun!</b>\n\nSilakan coba lagi atau hubungi admin.",
                reply_markup=keyboards.back_keyboard("menu_purchase"),
                parse_mode="HTML"
            )
            return
        
        # Deduct balance
        await database.update_user_balance(user['telegram_id'], -price_info['price'])
        
        # Record transaction
        await database.add_transaction(
            user_id=user['telegram_id'],
            tx_type="purchase",
            amount=-price_info['price'],
            description=f"Beli {protocol.upper()} {days} hari - {server['name']}"
        )
        
        # Save VPN account to database
        from vpn_manager import calculate_expiry
        expired_date = calculate_expiry(days)
        
        await database.add_vpn_account(
            user_id=user['telegram_id'],
            server_id=server_id,
            protocol=protocol,
            username=username,
            uuid=uuid,
            expired_date=expired_date,
            ip_limit=ip_limit,
            quota_gb=price_info['quota_gb'],
            password=uuid if protocol in ('ssh', 'shadowsocks') else None
        )
        
        # Show success message with account details
        account_info = {
            'protocol': protocol,
            'username': username,
            'uuid': uuid,
            'password': uuid if protocol in ('ssh', 'shadowsocks') else None,
            'expired_date': expired_date,
            'ip_limit': ip_limit,
            'status': 'active',
            'server_name': server['name']
        }
        
        text = f"""
✅ <b>PEMBELIAN BERHASIL!</b>

{formatter.account_detail_text(account_info, server['domain'])}

💰 Sisa Saldo: <b>{formatter.format_currency(fresh_user['balance'] - price_info['price'])}</b>
"""
        
        await query.edit_message_text(
            text,
            reply_markup=keyboards.back_keyboard("back_main"),
            parse_mode="HTML"
        )
        
    except Exception as e:
        await query.edit_message_text(
            f"❌ <b>Error:</b> {str(e)}\n\nHubungi admin jika masalah berlanjut.",
            reply_markup=keyboards.back_keyboard("back_main"),
            parse_mode="HTML"
        )


# ==================== ACCOUNTS ====================

@registered_user
@not_banned
async def my_accounts_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's VPN accounts"""
    query = update.callback_query
    await query.answer()
    
    user = context.user_data['db_user']
    accounts = await database.get_user_vpn_accounts(user['telegram_id'])
    
    if not accounts:
        await query.edit_message_text(
            """
╔══════════════════════════════╗
   📋 <b>AKUN SAYA</b> 📋
╚══════════════════════════════╝

<i>Anda belum memiliki akun VPN aktif.</i>
<i>Silakan beli akun melalui menu Beli Akun.</i>
""",
            reply_markup=keyboards.back_keyboard("back_main"),
            parse_mode="HTML"
        )
        return
    
    text = """
╔══════════════════════════════╗
   📋 <b>AKUN SAYA</b> 📋
╚══════════════════════════════╝

"""
    for acc in accounts:
        emoji = {"ssh": "🔵", "vmess": "🟢", "vless": "🟡", "trojan": "🔴", "shadowsocks": "🟣"}
        e = emoji.get(acc['protocol'], "📡")
        text += f"│ {e} <b>{acc['protocol'].upper()}</b> - {acc['username']}\n"
        text += f"│    Server: {acc.get('server_name', '-')} | Exp: {acc['expired_date']}\n\n"
    
    await query.edit_message_text(
        text,
        reply_markup=keyboards.back_keyboard("back_main"),
        parse_mode="HTML"
    )


# ==================== DEPOSIT ====================

@registered_user
@not_banned
async def deposit_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show deposit menu"""
    query = update.callback_query
    await query.answer()
    
    user = context.user_data['db_user']
    text = formatter.deposit_text(user['balance'])
    kb = keyboards.deposit_keyboard()
    
    await query.edit_message_text(text, reply_markup=kb, parse_mode="HTML")


@registered_user
@not_banned
async def deposit_qris_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show QRIS deposit amount selection"""
    query = update.callback_query
    await query.answer()
    
    text = formatter.deposit_qris_text(0)
    kb = keyboards.deposit_amount_keyboard()
    
    await query.edit_message_text(text, reply_markup=kb, parse_mode="HTML")


@registered_user
@not_banned
async def deposit_amount_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle deposit amount selection - create QRIS payment"""
    query = update.callback_query
    await query.answer("⏳ Membuat QRIS...")
    
    # Parse: dep_{amount}
    amount = int(query.data.replace("dep_", ""))
    user = context.user_data['db_user']
    
    from payment import create_qris_payment
    
    result = await create_qris_payment(amount, user['telegram_id'])
    
    if not result['success']:
        await query.edit_message_text(
            f"❌ <b>Gagal membuat pembayaran:</b>\n{result.get('error', 'Unknown error')}",
            reply_markup=keyboards.back_keyboard("menu_deposit"),
            parse_mode="HTML"
        )
        return
    
    # Save payment to database
    await database.create_payment(
        user_id=user['telegram_id'],
        amount=amount,
        payment_id=result.get('bayar_id', result['payment_id']),
        qris_url=result.get('qris_image', result.get('qris_url', ''))
    )
    
    text = formatter.payment_qris_text(amount, result['payment_id'])
    
    # Send QRIS image if available
    qris_image = result.get('qris_image', result.get('qris_url', ''))
    
    if qris_image:
        try:
            await query.message.delete()
            await context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=qris_image,
                caption=text,
                parse_mode="HTML",
                reply_markup=keyboards.back_keyboard("menu_deposit")
            )
        except Exception:
            await query.edit_message_text(
                text + f"\n\n🔗 <a href='{qris_image}'>Buka QRIS</a>",
                reply_markup=keyboards.back_keyboard("menu_deposit"),
                parse_mode="HTML"
            )
    else:
        await query.edit_message_text(
            text,
            reply_markup=keyboards.back_keyboard("menu_deposit"),
            parse_mode="HTML"
        )
    
    # Start payment checking job
    context.job_queue.run_repeating(
        check_payment_job,
        interval=10,
        first=10,
        data={
            "user_id": user['telegram_id'],
            "chat_id": query.message.chat_id,
            "payment_id": result.get('bayar_id', result['payment_id']),
            "amount": amount
        },
        name=f"payment_{user['telegram_id']}",
    )


async def check_payment_job(context: ContextTypes.DEFAULT_TYPE):
    """Background job to check payment status"""
    from payment import check_payment_status
    
    job_data = context.job.data
    payment_id = job_data['payment_id']
    user_id = job_data['user_id']
    chat_id = job_data['chat_id']
    amount = job_data['amount']
    
    result = await check_payment_status(payment_id)
    
    if result.get('paid'):
        # Payment successful
        await database.update_user_balance(user_id, amount)
        await database.update_payment_status(payment_id, "paid")
        await database.add_transaction(
            user_id=user_id,
            tx_type="topup",
            amount=amount,
            description=f"Deposit QRIS - {payment_id}",
            reference_id=payment_id
        )
        
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"""
✅ <b>DEPOSIT BERHASIL!</b>

💰 Nominal: <b>{formatter.format_currency(amount)}</b>
🆔 ID: <code>{payment_id}</code>

Saldo Anda telah ditambahkan.
Ketik /start untuk kembali ke menu.
""",
            parse_mode="HTML"
        )
        
        # Stop the job
        context.job.schedule_removal()


# ==================== VOUCHER ====================

@registered_user
@not_banned
async def voucher_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voucher redeem"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        """
╔══════════════════════════════╗
   🎫 <b>REDEEM VOUCHER</b> 🎫
╚══════════════════════════════╝

<i>Kirim kode voucher Anda:</i>
<i>(Ketik kode voucher di chat)</i>
""",
        reply_markup=keyboards.back_keyboard("back_main"),
        parse_mode="HTML"
    )
    context.user_data['waiting_for'] = 'voucher_code'


async def voucher_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voucher code text input"""
    if context.user_data.get('waiting_for') != 'voucher_code':
        return
    
    code = update.message.text.strip().upper()
    user_id = update.effective_user.id
    
    amount = await database.redeem_voucher(code, user_id)
    
    if amount:
        await database.update_user_balance(user_id, amount)
        await database.add_transaction(
            user_id=user_id,
            tx_type="voucher",
            amount=amount,
            description=f"Redeem voucher: {code}"
        )
        
        await update.message.reply_text(
            f"""
✅ <b>VOUCHER BERHASIL!</b>

🎫 Kode: <code>{code}</code>
💰 Nominal: <b>{formatter.format_currency(amount)}</b>

Saldo Anda telah ditambahkan.
Ketik /start untuk kembali ke menu.
""",
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(
            "❌ <b>Voucher tidak valid atau sudah digunakan.</b>",
            parse_mode="HTML"
        )
    
    context.user_data['waiting_for'] = None


# ==================== HISTORY ====================

@registered_user
@not_banned
async def history_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show transaction history"""
    query = update.callback_query
    await query.answer()
    
    user = context.user_data['db_user']
    transactions = await database.get_user_transactions(user['telegram_id'])
    
    text = formatter.transaction_history_text(transactions)
    
    await query.edit_message_text(
        text,
        reply_markup=keyboards.back_keyboard("back_main"),
        parse_mode="HTML"
    )


# ==================== SERVER INFO ====================

@registered_user
@not_banned
async def server_info_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show server information"""
    query = update.callback_query
    await query.answer()
    
    servers = await database.get_servers()
    text = formatter.server_info_text(servers)
    
    await query.edit_message_text(
        text,
        reply_markup=keyboards.back_keyboard("back_main"),
        parse_mode="HTML"
    )


# ==================== HELP ====================

@registered_user
@not_banned
async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help message"""
    query = update.callback_query
    await query.answer()
    
    text = formatter.help_text()
    
    await query.edit_message_text(
        text,
        reply_markup=keyboards.back_keyboard("back_main"),
        parse_mode="HTML"
    )
