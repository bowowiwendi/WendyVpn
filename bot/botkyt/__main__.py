"""Bot KYT - Wendy VPN Store Telegram Bot"""
import logging
import asyncio
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

import config
import database
import handlers
import admin_handlers

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def post_init(application):
    """Initialize database and set superadmin on startup"""
    await database.init_db()
    logger.info("Database initialized.")
    
    # Set superadmin
    if config.SUPER_ADMIN:
        try:
            admin_id = int(config.SUPER_ADMIN)
            user = await database.get_user(admin_id)
            if not user:
                await database.create_user(admin_id, role="superadmin")
            elif user['role'] != 'superadmin':
                await database.set_user_role(admin_id, "superadmin")
            logger.info(f"Super Admin set: {admin_id}")
        except (ValueError, TypeError):
            logger.warning(f"Invalid SUPER_ADMIN ID: {config.SUPER_ADMIN}")
    
    # Set default pricing if empty
    pricing = await database.get_pricing()
    if not pricing:
        defaults = [
            ("ssh", 7, 5000, 2, 0),
            ("ssh", 30, 10000, 2, 0),
            ("vmess", 7, 5000, 2, 0),
            ("vmess", 30, 10000, 2, 0),
            ("vless", 7, 5000, 2, 0),
            ("vless", 30, 10000, 2, 0),
            ("trojan", 7, 5000, 2, 0),
            ("trojan", 30, 10000, 2, 0),
            ("shadowsocks", 7, 5000, 2, 0),
            ("shadowsocks", 30, 10000, 2, 0),
        ]
        for proto, days, price, ip_limit, quota in defaults:
            await database.set_pricing(proto, days, price, ip_limit, quota)
        logger.info("Default pricing set.")


async def text_message_handler(update: Update, context):
    """Route text messages based on waiting_for state"""
    waiting = context.user_data.get('waiting_for')
    
    if waiting == 'voucher_code':
        await handlers.voucher_text_handler(update, context)
    elif waiting == 'admin_topup_userid':
        await admin_handlers.admin_topup_userid_handler(update, context)
    elif waiting == 'admin_topup_amount':
        await admin_handlers.admin_topup_amount_handler(update, context)
    elif waiting == 'admin_voucher_amount':
        await admin_handlers.admin_voucher_amount_handler(update, context)
    elif waiting == 'admin_pricing':
        await admin_handlers.admin_pricing_input_handler(update, context)
    elif waiting == 'admin_server':
        await admin_handlers.admin_server_input_handler(update, context)
    elif waiting == 'admin_broadcast':
        await admin_handlers.admin_broadcast_input_handler(update, context)
    elif waiting == 'admin_manage':
        await admin_handlers.admin_manage_input_handler(update, context)
    elif waiting == 'admin_users':
        await admin_handlers.admin_users_input_handler(update, context)


def main():
    """Start the bot"""
    if not config.BOT_TOKEN:
        logger.error("BOT_TOKEN not set! Please configure var.txt")
        return
    
    # Build application
    app = Application.builder().token(config.BOT_TOKEN).post_init(post_init).build()
    
    # Command handlers
    app.add_handler(CommandHandler("start", handlers.start_handler))
    app.add_handler(CommandHandler("menu", handlers.start_handler))
    
    # Callback query handlers - Main menu
    app.add_handler(CallbackQueryHandler(handlers.back_main_handler, pattern="^back_main$"))
    app.add_handler(CallbackQueryHandler(handlers.purchase_menu_handler, pattern="^menu_purchase$"))
    app.add_handler(CallbackQueryHandler(handlers.my_accounts_handler, pattern="^menu_accounts$"))
    app.add_handler(CallbackQueryHandler(handlers.deposit_menu_handler, pattern="^menu_deposit$"))
    app.add_handler(CallbackQueryHandler(handlers.history_handler, pattern="^menu_history$"))
    app.add_handler(CallbackQueryHandler(handlers.voucher_handler, pattern="^menu_voucher$"))
    app.add_handler(CallbackQueryHandler(handlers.server_info_handler, pattern="^menu_server_info$"))
    app.add_handler(CallbackQueryHandler(handlers.help_handler, pattern="^menu_help$"))
    
    # Callback query handlers - Purchase flow
    app.add_handler(CallbackQueryHandler(handlers.select_protocol_handler, pattern="^buy_"))
    app.add_handler(CallbackQueryHandler(handlers.select_server_handler, pattern="^server_"))
    app.add_handler(CallbackQueryHandler(handlers.select_duration_handler, pattern="^dur_"))
    app.add_handler(CallbackQueryHandler(handlers.confirm_purchase_handler, pattern="^confirm_buy_"))
    
    # Callback query handlers - Deposit
    app.add_handler(CallbackQueryHandler(handlers.deposit_qris_handler, pattern="^deposit_qris$"))
    app.add_handler(CallbackQueryHandler(handlers.deposit_amount_handler, pattern="^dep_"))
    
    # Callback query handlers - Admin
    app.add_handler(CallbackQueryHandler(admin_handlers.admin_panel_handler, pattern="^menu_admin$"))
    app.add_handler(CallbackQueryHandler(admin_handlers.admin_topup_handler, pattern="^admin_topup$"))
    app.add_handler(CallbackQueryHandler(admin_handlers.admin_voucher_handler, pattern="^admin_voucher$"))
    app.add_handler(CallbackQueryHandler(admin_handlers.admin_pricing_handler, pattern="^admin_pricing$"))
    app.add_handler(CallbackQueryHandler(admin_handlers.admin_servers_handler, pattern="^admin_servers$"))
    app.add_handler(CallbackQueryHandler(admin_handlers.admin_stats_handler, pattern="^admin_stats$"))
    app.add_handler(CallbackQueryHandler(admin_handlers.admin_broadcast_handler, pattern="^admin_broadcast$"))
    app.add_handler(CallbackQueryHandler(admin_handlers.admin_manage_admins_handler, pattern="^admin_manage_admins$"))
    app.add_handler(CallbackQueryHandler(admin_handlers.admin_users_handler, pattern="^admin_users$"))
    app.add_handler(CallbackQueryHandler(admin_handlers.admin_accounts_handler, pattern="^admin_accounts$"))
    
    # Noop handler for pagination info buttons
    app.add_handler(CallbackQueryHandler(lambda u, c: u.callback_query.answer(), pattern="^noop$"))
    
    # Text message handler (for input flows)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message_handler))
    
    # Start polling
    logger.info("Bot KYT starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
