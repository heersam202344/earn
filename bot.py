"""
PAGAL Escrow Bot 🤖
Main Application - python-telegram-bot v20 + Telethon
"""
import os
import sys
import logging
import asyncio
import random
import string
from datetime import datetime

from telegram import Update, BotCommand, InputFile
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

from config import BOT_TOKEN, ADMIN_IDS, ESCROW_FEE_DEFAULT, ADDRESS_EXPIRY_MINUTES, BOT_USERNAME, WALLETS
from database import Database
from keyboards import *
from texts import *
from photo_gen import generate_group_photo
from telethon_manager import telethon_mgr
from utils import auto_correct_command, get_fee_for_users

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

db = Database()

# ==================== STARTUP ====================
async def post_init(application: Application):
    """Set bot commands menu"""
    commands = [
        BotCommand("start", "Start the bot"),
        BotCommand("menu", "Show main menu"),
        BotCommand("escrow", "Create new escrow (in group)"),
        BotCommand("dd", "Fill Deal Details"),
        BotCommand("buyer", "Set buyer address"),
        BotCommand("seller", "Set seller address"),
        BotCommand("token", "Choose cryptocurrency"),
        BotCommand("deposit", "Get deposit address"),
        BotCommand("release", "Release funds to buyer"),
        BotCommand("refund", "Refund funds to seller"),
        BotCommand("dispute", "Raise a dispute"),
    ]
    await application.bot.set_my_commands(commands)

    # Connect Telethon
    connected = await telethon_mgr.connect()
    if connected:
        logger.info("✅ Telethon connected successfully")
    else:
        logger.warning("⚠️ Telethon not connected - auto group creation disabled")

async def post_shutdown(application: Application):
    await telethon_mgr.disconnect()

# ==================== PRIVATE CHAT HANDLERS ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start in DM - Screenshot #1"""
    user = update.effective_user
    db.add_user(user.id, user.username, user.first_name)

    await update.message.reply_text(WELCOME_TEXT, reply_markup=welcome_keyboard())
    await update.message.reply_text(ESCROW_TYPE_TEXT, reply_markup=escrow_type_keyboard())

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/menu command"""
    await update.message.reply_text(WELCOME_TEXT, reply_markup=welcome_keyboard())
    await update.message.reply_text(ESCROW_TYPE_TEXT, reply_markup=escrow_type_keyboard())

# ==================== GROUP HANDLERS ====================
async def escrow_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /escrow in group - Initialize escrow
    Screenshot #3: Escrow Group Created message
    """
    if update.effective_chat.type == 'private':
        await update.message.reply_text(
            "❌ This command only works in groups!\n\n"
            "Click P2P below to auto-create an escrow group:",
            reply_markup=escrow_type_keyboard()
        )
        return

    group_id = update.effective_chat.id
    creator = update.effective_user

    existing = db.get_escrow_by_group(group_id)
    if existing:
        await update.message.reply_text("❌ An escrow already exists in this group!")
        return

    group_name = update.effective_chat.title or "Escrow Group"
    escrow_id = db.create_escrow(
        group_id, creator.id, creator.username, 
        creator.first_name, group_name
    )

    # Generate invite link via Bot API
    try:
        link_obj = await context.bot.create_chat_invite_link(
            group_id, member_limit=2, name=f"Escrow-{escrow_id}"
        )
        db.update_escrow(escrow_id, invite_link=link_obj.invite_link)
        invite_link = f'<a href="{link_obj.invite_link}">{link_obj.invite_link}</a>'
    except Exception as e:
        logger.error(f"Invite link error: {e}")
        invite_link = "Link unavailable"

    await update.message.reply_text(
        GROUP_CREATED_TEXT.format(creator_name=creator.first_name, invite_link=invite_link),
        parse_mode='HTML',
        disable_web_page_preview=True
    )

    # Pin welcome message (Screenshot #4)
    pin_msg = await context.bot.send_message(group_id, GROUP_WELCOME_PIN)
    await context.bot.pin_chat_message(group_id, pin_msg.message_id)
    db.add_message_id(escrow_id, pin_msg.message_id)

    # Send start instruction
    await context.bot.send_message(group_id, GROUP_START_TEXT)

async def dd_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /dd - Deal Details
    Screenshot #5: Group name changes + deal details text
    """
    if update.effective_chat.type == 'private':
        await update.message.reply_text("❌ This command only works in escrow groups!")
        return

    group_id = update.effective_chat.id
    escrow = db.get_escrow_by_group(group_id)
    if not escrow:
        await update.message.reply_text("❌ No active escrow in this group! Start with /escrow")
        return

    db.update_escrow(escrow['escrow_id'], status='awaiting_dd')

    # Change group name (Screenshot #5)
    new_title = f"P2P Escrow By PAGAL Bot ({escrow['escrow_id']})"
    try:
        await context.bot.set_chat_title(group_id, new_title)
    except Exception as e:
        logger.error(f"Title change error: {e}")

    await update.message.reply_text(DD_TEXT, reply_markup=how_to_use_keyboard())

async def buyer_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /buyer [ADDRESS] - Set buyer wallet
    Screenshot #6
    """
    if update.effective_chat.type == 'private':
        return

    group_id = update.effective_chat.id
    escrow = db.get_escrow_by_group(group_id)
    if not escrow:
        return

    args = context.args
    if not args:
        await update.message.reply_text("❌ Usage: <code>/buyer [CRYPTO ADDRESS]</code>", parse_mode='HTML')
        return

    wallet = args[0]
    user = update.effective_user

    db.set_buyer(escrow['escrow_id'], user.id, user.username or user.first_name, wallet)

    text = buyer_declared_text(
        user.username or user.first_name,
        user.id,
        wallet
    )
    await update.message.reply_text(text, parse_mode='HTML')
    await update.message.reply_text("Please set seller using <code>/seller [DEPOSIT ADDRESS]</code>", parse_mode='HTML')

async def seller_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /seller [ADDRESS] - Set seller wallet
    Screenshot #7-8
    """
    if update.effective_chat.type == 'private':
        return

    group_id = update.effective_chat.id
    escrow = db.get_escrow_by_group(group_id)
    if not escrow:
        return

    args = context.args
    if not args:
        await update.message.reply_text("❌ Usage: <code>/seller [DEPOSIT ADDRESS]</code>", parse_mode='HTML')
        return

    wallet = args[0]
    user = update.effective_user

    db.set_seller(escrow['escrow_id'], user.id, user.username or user.first_name, wallet)

    text = seller_declared_text(
        user.username or user.first_name,
        user.id,
        wallet
    )
    await update.message.reply_text(text, parse_mode='HTML')
    await update.message.reply_text(TOKEN_PROMPT)

async def token_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /token - Choose crypto
    Screenshot #9
    """
    if update.effective_chat.type == 'private':
        return

    group_id = update.effective_chat.id
    escrow = db.get_escrow_by_group(group_id)
    if not escrow:
        return

    if escrow['status'] not in ['awaiting_token', 'awaiting_seller', 'awaiting_network']:
        await update.message.reply_text("❌ Set buyer and seller first!")
        return

    await update.message.reply_text("choose token from the list below", reply_markup=token_keyboard())

async def deposit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /deposit - Generate deposit address
    Screenshot #15-16
    """
    if update.effective_chat.type == 'private':
        return

    group_id = update.effective_chat.id
    escrow = db.get_escrow_by_group(group_id)
    if not escrow or escrow['status'] != 'active':
        await update.message.reply_text("❌ Escrow not active yet! Complete setup first.")
        return

    await update.message.reply_text(deposit_request_text())

    # Generate escrow address based on selected crypto
    token = escrow.get('token', 'USDT')
    network = escrow.get('network', 'BSC')

    if token == 'BTC':
        escrow_address = WALLETS.get('BTC', 'bc1qkn9ufppulzlhkxa46hrspnd4l24s9px9pxuxet')
    elif token == 'LTC':
        escrow_address = WALLETS.get('LTC', 'ltc1q8ywwttdd87s2h8ytr7d5ncc7029kjadrwvxph7')
    elif token == 'USDT' and network == 'BSC':
        escrow_address = WALLETS.get('USDT_BSC', '0x16091F2b5F3FA0EA1B384DfA16b37316bac4FCB2')
    elif token == 'USDT' and network == 'TRON':
        escrow_address = WALLETS.get('USDT_TRC', '0x16091F2b5F3FA0EA1B384DfA16b37316bac4FCB2')
    else:
        escrow_address = WALLETS.get('USDT_BSC', '0x16091F2b5F3FA0EA1B384DfA16b37316bac4FCB2')

    db.set_escrow_address(escrow['escrow_id'], escrow_address)

    text = deposit_info_text(
        escrow_id=escrow['escrow_id'],
        seller_username=escrow['seller_username'],
        seller_id=escrow['seller_id'],
        seller_wallet=escrow['seller_wallet'],
        buyer_username=escrow['buyer_username'],
        buyer_id=escrow['buyer_id'],
        buyer_wallet=escrow['buyer_wallet'],
        escrow_address=escrow_address,
        token=escrow['token'],
        network=escrow['network'],
        trade_time=escrow['trade_start_time'],
        expiry_minutes=ADDRESS_EXPIRY_MINUTES
    )

    msg = await update.message.reply_text(text, reply_markup=check_payment_keyboard(), parse_mode='HTML')

    # Pin transaction info (Screenshot #16)
    await context.bot.pin_chat_message(group_id, msg.message_id)
    db.add_message_id(escrow['escrow_id'], msg.message_id)

async def release_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == 'private':
        return

    group_id = update.effective_chat.id
    escrow = db.get_escrow_by_group(group_id)
    if not escrow:
        return

    db.complete_escrow(escrow['escrow_id'])
    await update.message.reply_text(
        f"✅ <b>Funds Released!</b>\n\n"
        f"Funds have been released to buyer @{escrow['buyer_username']}.\n"
        f"Transaction complete. Thank you for using PAGAL Escrow Bot 🤖",
        parse_mode='HTML'
    )

async def refund_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == 'private':
        return

    group_id = update.effective_chat.id
    escrow = db.get_escrow_by_group(group_id)
    if not escrow:
        return

    db.refund_escrow(escrow['escrow_id'])
    await update.message.reply_text(
        f"✅ <b>Funds Refunded!</b>\n\n"
        f"Funds have been refunded to seller @{escrow['seller_username']}.\n"
        f"Transaction refunded. Thank you for using PAGAL Escrow Bot 🤖",
        parse_mode='HTML'
    )

async def dispute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat

    await update.message.reply_text(
        "🚨 <b>Dispute Raised!</b>\n\n"
        "An arbitrator will join the group chat within 24 hours.\n"
        "Please do not send funds until the dispute is resolved.",
        parse_mode='HTML'
    )

    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                admin_id,
                f"🚨 <b>DISPUTE ALERT</b>\n\n"
                f"User: @{user.username or user.first_name} [<code>{user.id}</code>]\n"
                f"Chat: {chat.title}\n"
                f"Chat ID: <code>{chat.id}</code>",
                parse_mode='HTML'
            )
        except Exception as e:
            logger.error(f"Failed to notify admin {admin_id}: {e}")

# ==================== CALLBACK HANDLERS ====================
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user = update.effective_user
    chat = update.effective_chat

    # Private chat callbacks
    if data == 'commands_list':
        await query.message.reply_text(commands_list_text(), parse_mode='HTML')

    elif data == 'contact':
        await query.message.reply_text(CONTACT_TEXT, parse_mode='HTML')

    elif data == 'what_is_escrow':
        await query.message.reply_text(WHAT_IS_ESCROW_TEXT, parse_mode='HTML')

    elif data == 'instructions':
        await query.message.reply_text(INSTRUCTIONS_TEXT, parse_mode='HTML')

    elif data == 'terms':
        await query.message.reply_text(TERMS_TEXT, parse_mode='HTML')

    elif data == 'invites':
        await query.message.reply_text(INVITES_TEXT, parse_mode='HTML')

    elif data == 'how_to_use':
        await query.message.reply_text(INSTRUCTIONS_TEXT, parse_mode='HTML')

    elif data == 'escrow_p2p':
        # Screenshot #2: "Creating a safe trading place..."
        await query.message.reply_text(CREATING_ESCROW_TEXT)

        if telethon_mgr.connected:
            # Auto-create group via Telethon
            group_id, invite_link = await telethon_mgr.create_escrow_group(user.id, 0)
            if group_id:
                await query.message.reply_text(
                    f"📍 <b>Escrow Group Created!</b>\n\n"
                    f"Group ID: <code>{group_id}</code>\n"
                    f"Link: {invite_link or 'N/A'}\n\n"
                    f"Join the group and send /escrow to start!",
                    parse_mode='HTML'
                )
            else:
                await query.message.reply_text(
                    "⚠️ Auto-creation failed. Please manually:\n"
                    "1️⃣ Create a group\n"
                    "2️⃣ Add me as admin\n"
                    "3️⃣ Send /escrow"
                )
        else:
            await query.message.reply_text(
                "📍 <b>To create a P2P Escrow:</b>\n\n"
                "1️⃣ Create a new group\n"
                "2️⃣ Add @PagaLEscrowBot as admin\n"
                "3️⃣ Send /escrow in the group",
                parse_mode='HTML'
            )

    elif data == 'escrow_product':
        await query.message.reply_text("🛍️ <b>Product Deal</b> feature coming soon!", parse_mode='HTML')

    # Group chat callbacks
    elif data.startswith('token_'):
        token = data.split('_')[1]
        group_id = chat.id
        escrow = db.get_escrow_by_group(group_id)
        if not escrow:
            return

        db.set_token(escrow['escrow_id'], token)

        text = crypto_declaration_text(token)
        await query.message.reply_text(text, reply_markup=network_keyboard(token), parse_mode='HTML')

    elif data == 'back_token':
        await query.message.reply_text("choose token from the list below", reply_markup=token_keyboard())

    elif data.startswith('net_'):
        network = data.split('_')[1]
        group_id = chat.id
        escrow = db.get_escrow_by_group(group_id)
        if not escrow:
            return

        db.set_network(escrow['escrow_id'], network)
        escrow = db.get_escrow_by_id(escrow['escrow_id'])

        text = escrow_declaration_text(
            escrow['seller_username'],
            escrow['seller_id'],
            escrow['token'],
            network
        )
        await query.message.reply_text(text, reply_markup=accept_reject_keyboard(), parse_mode='HTML')

    elif data == 'accept_escrow':
        group_id = chat.id
        escrow = db.get_escrow_by_group(group_id)
        if not escrow:
            return

        db.accept_escrow(escrow['escrow_id'])
        escrow = db.get_escrow_by_id(escrow['escrow_id'])

        # Full declaration (Screenshot #13)
        text = full_declaration_text(
            escrow['buyer_username'],
            escrow['buyer_id'],
            escrow['seller_username'],
            escrow['seller_id'],
            escrow['token'],
            escrow['network']
        )
        await query.message.reply_text(text, parse_mode='HTML')

        # Transaction info (Screenshot #14)
        trans_text = transaction_info_text(
            escrow['escrow_id'],
            escrow['seller_username'],
            escrow['seller_id'],
            escrow['seller_wallet'],
            escrow['buyer_username'],
            escrow['buyer_id'],
            escrow['buyer_wallet'],
            escrow['token'],
            escrow['network'],
            escrow['trade_start_time']
        )
        await query.message.reply_text(trans_text, parse_mode='HTML')

        # Change group photo (Screenshot #12)
        try:
            photo_path = generate_group_photo(
                escrow['buyer_username'] or 'buyer',
                escrow['seller_username'] or 'seller'
            )
            if photo_path and os.path.exists(photo_path):
                with open(photo_path, 'rb') as f:
                    await context.bot.set_chat_photo(group_id, photo=f)

                # Also try Telethon for better control
                if telethon_mgr.connected:
                    await telethon_mgr.change_group_photo(group_id, photo_path)
        except Exception as e:
            logger.error(f"Photo change error: {e}")

        # Fee notice (Screenshot #14 bottom)
        buyer = db.get_user(escrow['buyer_id'])
        seller = db.get_user(escrow['seller_id'])
        fee = get_fee_for_users(
            buyer.get('bio', '') if buyer else '',
            seller.get('bio', '') if seller else ''
        )
        await query.message.reply_text(fee_notice_text(fee), parse_mode='HTML')

    elif data == 'reject_escrow':
        await query.message.reply_text(
            "❌ <b>Escrow Rejected</b>\n\nStart over with /escrow",
            parse_mode='HTML'
        )

    elif data == 'check_payment':
        await query.message.reply_text(
            "🔍 <b>Checking Payment...</b>\n\n"
            "⏳ Please wait while we verify the transaction.\n"
            "If payment is confirmed, the seller can click /release to send funds to buyer.",
            parse_mode='HTML'
        )

# ==================== AUTO-CORRECTION ====================
async def auto_correct_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle unknown/misspelled commands"""
    if not update.message or not update.message.text:
        return

    text = update.message.text
    corrected, cmd = auto_correct_command(text)

    if corrected and cmd:
        await update.message.reply_text(
            AUTO_CORRECT_TEXT.format(corrected=corrected, cmd=cmd),
            parse_mode='HTML'
        )

        # Route to correct handler
        if cmd == 'escrow':
            await escrow_command(update, context)
        elif cmd == 'dd':
            await dd_command(update, context)
        elif cmd == 'buyer':
            context.args = text.split()[1:]
            await buyer_command(update, context)
        elif cmd == 'seller':
            context.args = text.split()[1:]
            await seller_command(update, context)
        elif cmd == 'token':
            await token_command(update, context)
        elif cmd == 'deposit':
            await deposit_command(update, context)
        elif cmd == 'release':
            await release_command(update, context)
        elif cmd == 'refund':
            await refund_command(update, context)
        elif cmd == 'dispute':
            await dispute_command(update, context)

# ==================== MAIN ====================
def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", menu))
    application.add_handler(CommandHandler("escrow", escrow_command))
    application.add_handler(CommandHandler("dd", dd_command))
    application.add_handler(CommandHandler("buyer", buyer_command))
    application.add_handler(CommandHandler("seller", seller_command))
    application.add_handler(CommandHandler("token", token_command))
    application.add_handler(CommandHandler("deposit", deposit_command))
    application.add_handler(CommandHandler("release", release_command))
    application.add_handler(CommandHandler("refund", refund_command))
    application.add_handler(CommandHandler("dispute", dispute_command))

    # Callbacks
    application.add_handler(CallbackQueryHandler(button_callback))

    # Auto-correction for unknown commands
    application.add_handler(MessageHandler(filters.COMMAND, auto_correct_handler))

    application.post_init = post_init
    application.post_shutdown = post_shutdown

    logger.info("🤖 PAGAL Escrow Bot starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
