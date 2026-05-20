"""Decorators for access control"""
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
import database


def registered_user(func):
    """Decorator to ensure user is registered"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        db_user = await database.get_user(user.id)
        
        if not db_user:
            await database.create_user(
                telegram_id=user.id,
                username=user.username,
                full_name=user.full_name
            )
            db_user = await database.get_user(user.id)
        
        context.user_data['db_user'] = db_user
        return await func(update, context, *args, **kwargs)
    
    return wrapper


def admin_only(func):
    """Decorator to restrict access to admins only"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        db_user = await database.get_user(user.id)
        
        if not db_user or db_user['role'] not in ('admin', 'superadmin'):
            if update.callback_query:
                await update.callback_query.answer("⛔ Akses ditolak! Hanya admin.", show_alert=True)
            else:
                await update.message.reply_text("⛔ Akses ditolak! Hanya admin.")
            return
        
        context.user_data['db_user'] = db_user
        return await func(update, context, *args, **kwargs)
    
    return wrapper


def superadmin_only(func):
    """Decorator to restrict access to superadmin only"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        db_user = await database.get_user(user.id)
        
        if not db_user or db_user['role'] != 'superadmin':
            if update.callback_query:
                await update.callback_query.answer("⛔ Akses ditolak! Hanya Super Admin.", show_alert=True)
            else:
                await update.message.reply_text("⛔ Akses ditolak! Hanya Super Admin.")
            return
        
        context.user_data['db_user'] = db_user
        return await func(update, context, *args, **kwargs)
    
    return wrapper


def not_banned(func):
    """Decorator to check if user is banned"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        db_user = await database.get_user(user.id)
        
        if db_user and db_user['is_banned']:
            if update.callback_query:
                await update.callback_query.answer("🚫 Akun Anda telah diblokir.", show_alert=True)
            else:
                await update.message.reply_text("🚫 Akun Anda telah diblokir. Hubungi admin.")
            return
        
        return await func(update, context, *args, **kwargs)
    
    return wrapper
