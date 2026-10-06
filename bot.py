import os
import logging
from threading import Thread
from flask import Flask
import logging as flask_logging
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatMemberStatus, ParseMode
from telegram.ext import (
    Application,
    ChatJoinRequestHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    CallbackQueryHandler
)

# ==========================================
# 0. Logging Setup
# ==========================================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration Variables
BOT_TOKEN = "8975293007:AAFUW1bxU1w-Vgxo8f5JjGLSlrtCk0y2sVA"
ADMIN_ID = 8858060392

# Ekhane Channel Username Gulo Deya Holo
CHANNELS = ["@realonlineincomebd2", "@rksystemx"]
CHANNEL_LINKS = ["https://t.me/realonlineincomebd2", "https://t.me/rksystemx"]

# ==========================================
# 1. Web Server (Render/Termux 24/7 Active)
# ==========================================
def keep_alive():
    try:
        web_app = Flask(__name__)

        @web_app.route('/')
        def home():
            return "Bot is alive and running!"

        def run_web():
            log = flask_logging.getLogger('werkzeug')
            log.setLevel(flask_logging.ERROR)
            port = int(os.environ.get("PORT", 8080))
            web_app.run(host="0.0.0.0", port=port)

        t = Thread(target=run_web)
        t.daemon = True
        t.start()
        logger.info("Web server started successfully.")
    except Exception as e:
        logger.warning(f"Web server could not start. Error: {e}")

# ==========================================
# 2. Advanced Membership Check & UI Logic
# ==========================================

async def post_init(application: Application):
    try:
        await application.bot.send_message(
            chat_id=ADMIN_ID,
            text="🟢 *Bot is now Online!*\n\nAll systems are running perfectly. Ready to approve requests and verify users.",
            parse_mode=ParseMode.MARKDOWN
        )
        logger.info("Startup message sent to admin successfully.")
    except Exception as e:
        logger.error(f"Could not send startup message: {e}")

async def check_membership(bot, user_id):
    if user_id == ADMIN_ID:
        return True  # Admin er jonno bypass
    
    for channel in CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel, user_id=user_id)
            # Official ChatMemberStatus use kora hoyeche perfect detection er jonno
            if member.status not in [
                ChatMemberStatus.MEMBER, 
                ChatMemberStatus.ADMINISTRATOR, 
                ChatMemberStatus.OWNER,
                ChatMemberStatus.RESTRICTED
            ]:
                return False
        except Exception as e:
            logger.error(f"User {user_id} not found in {channel}: {e}")
            return False
    return True

def get_force_sub_keyboard():
    keyboard = [
        [InlineKeyboardButton("📢 Join Channel 1", url=CHANNEL_LINKS[0])],
        [InlineKeyboardButton("📢 Join Channel 2", url=CHANNEL_LINKS[1])],
        [InlineKeyboardButton("🔄 Check & Verify", callback_data="check_sub")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_main_menu_keyboard():
    keyboard = [
        ['🚀 Bot Status', 'ℹ️ Help'],
        ['👨‍💻 Admin Panel']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def send_main_menu(context_or_update, user, is_callback=False):
    welcome_msg = (
        f"🌟 *Welcome,* {user.first_name}!\n\n"
        "✅ *You are verified!* I am ready to auto-approve new members in your group. Just add me as an Admin with `Invite Users` permission.\n\n"
        "👇 *Select an option from the menu below:*"
    )
    
    if is_callback:
        await context_or_update.bot.send_message(
            chat_id=user.id, 
            text=welcome_msg, 
            reply_markup=get_main_menu_keyboard(), 
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        await context_or_update.message.reply_text(
            text=welcome_msg, 
            reply_markup=get_main_menu_keyboard(), 
            parse_mode=ParseMode.MARKDOWN
        )

# ==========================================
# 3. Telegram Bot Handlers
# ==========================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    is_member = await check_membership(context.bot, user.id)
    
    if not is_member:
        msg = (
            f"🛑 *Access Denied, {user.first_name}!*\n\n"
            "To use this bot, you MUST join our official channels.\n"
            "1️⃣ Join both channels from the buttons below.\n"
            "2️⃣ Click on *Check & Verify*."
        )
        await update.message.reply_text(msg, reply_markup=get_force_sub_keyboard(), parse_mode=ParseMode.MARKDOWN)
        return
    
    await send_main_menu(update, user, is_callback=False)

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text
    
    is_member = await check_membership(context.bot, user.id)
    if not is_member:
        await update.message.reply_text(
            "🛑 *You left the channels!*\nPlease join our channels again to continue using the bot.",
            reply_markup=get_force_sub_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
        return

    if text == '🚀 Bot Status':
        await update.message.reply_text("✅ *All systems are operational!*\nI am running 24/7 and ready to approve members.", parse_mode=ParseMode.MARKDOWN)
    
    elif text == 'ℹ️ Help':
        help_text = (
            "🛠 *How to setup in your group:*\n\n"
            "1️⃣ Add me to your private group.\n"
            "2️⃣ Make me an Admin.\n"
            "3️⃣ Ensure I have the `Invite Users` permission.\n"
            "4️⃣ Turn on `Request admin approval` in the group's invite link settings.\n\n"
            "*Commands:*\n"
            "`/start` - Restart bot"
        )
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    elif text == '👨‍💻 Admin Panel':
        if user.id == ADMIN_ID:
            keyboard = [[InlineKeyboardButton("⚠️️ Approve Pending Requests", callback_data='approve_all')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text("👑 *Welcome Admin!*\nWhat would you like to do?", reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text("⛔ *Access Restricted.*\nYou are not authorized to access this panel.", parse_mode=ParseMode.MARKDOWN)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = update.effective_user
    await query.answer()

    if query.data == 'check_sub':
        is_member = await check_membership(context.bot, user.id)
        if is_member:
            await query.message.delete() # Purono message delete kore dibe
            await send_main_menu(context, user, is_callback=True)
        else:
            await context.bot.send_message(
                chat_id=user.id,
                text="❌ *Verification Failed!*\nMake sure you joined BOTH channels before clicking Verify.",
                reply_markup=get_force_sub_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )

    elif query.data == 'approve_all':
        msg = (
            "⚠️ *Important Note about Past Requests:*\n\n"
            "The Telegram Bot API *does not* allow bots to fetch or approve join requests that were made _before_ the bot was added or activated.\n\n"
            "However, from now on, any *new* requests will be approved instantly! ⚡"
        )
        await query.edit_message_text(msg, parse_mode=ParseMode.MARKDOWN)

async def approve_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.chat_join_request.approve()
        user = update.chat_join_request.from_user
        chat = update.chat_join_request.chat
        
        logger.info(f"Approved user: {user.first_name} in {chat.title}")
        
        if ADMIN_ID:
            log_msg = f"✅ *Auto-Approved:* [{user.first_name}](tg://user?id={user.id}) in '{chat.title}'"
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=log_msg,
                parse_mode=ParseMode.MARKDOWN
            )
    except Exception as e:
        logger.error(f"Approval error: {e}")

def main():
    keep_alive()

    try:
        app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))
        app.add_handler(ChatJoinRequestHandler(approve_request))
        app.add_handler(CallbackQueryHandler(button_handler))

        logger.info("Bot is starting...")
        
        app.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        logger.error(f"Bot failed to start. Error: {e}")

if __name__ == '__main__':
    main()

