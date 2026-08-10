"""
PAGAL Escrow Bot 🤖
Recreated exactly from screenshots
Telegram: @PagaLEscrowBot
"""

import logging
import sqlite3
import os
import random
import string
from datetime import datetime, timedelta
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    BotCommand, InputFile
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

# ==================== CONFIG ====================
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
ADMIN_IDS = [123456789]  # Add your admin IDs here for dispute alerts
ESCROW_FEE_DEFAULT = 1.0
ESCROW_FEE_PROMO = 0.0   # If both have @PagaLEscrowBot in bio
ADDRESS_EXPIRY_MINUTES = 20
DB_NAME = "pagal_escrow.db"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ==================== DATABASE ====================
class Database:
    def __init__(self, db_name=DB_NAME):
        self.db_name = db_name
        self.init_db()

    def get_conn(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                bio TEXT,
                has_bot_in_bio INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS escrows (
                escrow_id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER UNIQUE,
                creator_id INTEGER,
                creator_username TEXT,
                buyer_id INTEGER,
                buyer_username TEXT,
                buyer_wallet TEXT,
                seller_id INTEGER,
                seller_username TEXT,
                seller_wallet TEXT,
                token TEXT,
                network TEXT,
                deal_details TEXT,
                status TEXT DEFAULT 'pending',
                escrow_address TEXT,
                amount_received REAL DEFAULT 0,
                trade_start_time TEXT,
                fee_percent REAL DEFAULT 1.0,
                invite_link TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS saved_wallets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                token TEXT,
                network TEXT,
                address TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def add_user(self, user_id, username, bio=""):
        conn = self.get_conn()
        cur = conn.cursor()
        has_bot = 1 if "@PagaLEscrowBot" in (bio or "") else 0
        cur.execute('''
            INSERT OR REPLACE INTO users (user_id, username, bio, has_bot_in_bio)
            VALUES (?, ?, ?, ?)
        ''', (user_id, username, bio, has_bot))
        conn.commit()
        conn.close()

    def get_user(self, user_id):
        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

    def create_escrow(self, group_id, creator_id, creator_username):
        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO escrows (group_id, creator_id, creator_username, status)
            VALUES (?, ?, ?, 'pending')
        ''', (group_id, creator_id, creator_username))
        eid = cur.lastrowid
        conn.commit()
        conn.close()
        return eid

    def get_escrow_by_group(self, group_id):
        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM escrows WHERE group_id = ?", (group_id,))
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_escrow_by_id(self, escrow_id):
        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM escrows WHERE escrow_id = ?", (escrow_id,))
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

    def update_escrow(self, escrow_id, **kwargs):
        conn = self.get_conn()
        cur = conn.cursor()
        for key, value in kwargs.items():
            cur.execute(f"UPDATE escrows SET {key} = ? WHERE escrow_id = ?", (value, escrow_id))
        conn.commit()
        conn.close()

    def set_deal_details(self, escrow_id, details):
        self.update_escrow(escrow_id, deal_details=details, status='awaiting_buyer')

    def set_buyer(self, escrow_id, buyer_id, buyer_username, buyer_wallet):
        self.update_escrow(escrow_id, buyer_id=buyer_id, buyer_username=buyer_username,
                           buyer_wallet=buyer_wallet, status='awaiting_seller')

    def set_seller(self, escrow_id, seller_id, seller_username, seller_wallet):
        self.update_escrow(escrow_id, seller_id=seller_id, seller_username=seller_username,
                           seller_wallet=seller_wallet, status='awaiting_token')

    def set_token(self, escrow_id, token):
        self.update_escrow(escrow_id, token=token, status='awaiting_network')

    def set_network(self, escrow_id, network):
        self.update_escrow(escrow_id, network=network, status='awaiting_accept')

    def accept_escrow(self, escrow_id):
        now = datetime.now().strftime("%d/%m/%y %H:%M:%S")
        self.update_escrow(escrow_id, status='active', trade_start_time=now)

    def set_escrow_address(self, escrow_id, address):
        self.update_escrow(escrow_id, escrow_address=address, status='deposited')

    def save_wallet(self, user_id, token, network, address):
        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute('''
            INSERT OR REPLACE INTO saved_wallets (user_id, token, network, address)
            VALUES (?, ?, ?, ?)
        ''', (user_id, token, network, address))
        conn.commit()
        conn.close()


db = Database()


# ==================== PHOTO GENERATOR ====================
def generate_group_photo(buyer_username, seller_username, output_path="group_photo.png"):
    """
    Generates the group photo with buyer/seller names overlaid.
    USER: Replace 'template.png' with your actual template image path.
    USER: Replace 'font.ttf' with your actual font file path.
    """
    try:
        # Open template (USER: provide your template image)
        template_path = "template.png"  # <-- CHANGE THIS
        font_path = "font.ttf"          # <-- CHANGE THIS (match screenshot font)
        
        img = Image.open(template_path).convert("RGBA")
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype(font_path, 36)
        except:
            font = ImageFont.load_default()
        
        # These coordinates are placeholders - ADJUST according to your template
        # The screenshot shows text at bottom: "💰 BUYER: @cixxu" and "💰 SELLER: @supanz"
        draw.text((150, 500), f"💰 BUYER: @{buyer_username}", fill="white", font=font)
        draw.text((150, 550), f"💰 SELLER: @{seller_username}", fill="white", font=font)
        
        img.save(output_path)
        return output_path
    except Exception as e:
        logger.error(f"Photo generation failed: {e}")
        return None


# ==================== AUTO-CORRECTION ====================
KNOWN_COMMANDS = ['start', 'menu', 'escrow', 'dd', 'buyer', 'seller', 
                  'token', 'deposit', 'release', 'refund', 'dispute']

def auto_correct_command(text):
    """Auto-corrects misspelled commands like /byer -> /buyer"""
    if not text or not text.startswith('/'):
        return None, None
    
    parts = text[1:].split()
    raw_cmd = parts[0].split('@')[0].lower()
    args = parts[1:] if len(parts) > 1 else []
    
    if raw_cmd in KNOWN_COMMANDS:
        return None, None  # No correction needed
    
    import difflib
    matches = difflib.get_close_matches(raw_cmd, KNOWN_COMMANDS, n=1, cutoff=0.6)
    if matches:
        corrected = '/' + matches[0]
        if args:
            corrected += ' ' + ' '.join(args)
        # Preserve @botname if present
        if '@' in parts[0]:
            corrected += '@' + parts[0].split('@')[1]
        return corrected, matches[0]
    
    return None, None


# ==================== KEYBOARD MARKUPS ====================
def welcome_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("COMMANDS LIST 🤖", callback_data='commands_list')],
        [InlineKeyboardButton("☎️ CONTACT", callback_data='contact')],
        [InlineKeyboardButton("Updates ⤴️", url="https://t.me/updates"),
         InlineKeyboardButton("Vouchers ✅", url="https://t.me/vouchers")],
        [InlineKeyboardButton("WHAT IS ESCROW ❓", callback_data='what_is_escrow'),
         InlineKeyboardButton("Instructions 👨‍💻", callback_data='instructions')],
        [InlineKeyboardButton("Terms 📝", callback_data='terms')],
        [InlineKeyboardButton("Invites 👤", callback_data='invites')]
    ])

def escrow_type_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("P2P", callback_data='p2p'),
         InlineKeyboardButton("Product Deal", callback_data='product_deal')]
    ])

def token_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("LTC", callback_data='token_ltc'),
         InlineKeyboardButton("BTC", callback_data='token_btc')],
        [InlineKeyboardButton("USDT", callback_data='token_usdt')]
    ])

def network_keyboard(token):
    networks = {
        'USDT': [InlineKeyboardButton("BSC[BEP20]", callback_data='net_bsc'),
                 InlineKeyboardButton("TRON[TRC20]", callback_data='net_tron')],
        'BTC': [InlineKeyboardButton("BTC Network", callback_data='net_btc')],
        'LTC': [InlineKeyboardButton("LTC Network", callback_data='net_ltc')]
    }
    buttons = networks.get(token, networks['USDT'])
    return InlineKeyboardMarkup([
        buttons,
        [InlineKeyboardButton("Back ⬅️", callback_data='back_token')]
    ])

def accept_reject_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Accept ✅", callback_data='accept_escrow'),
         InlineKeyboardButton("Reject ❌", callback_data='reject_escrow')]
    ])

def check_payment_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Check Payment", callback_data='check_payment')]
    ])


# ==================== MESSAGE TEXTS ====================
WELCOME_TEXT = """💫 @PagaLEscrowBot 💫
Your Trustworthy Telegram Escrow Service

Welcome to @PagaLEscrowBot. This bot provides a reliable escrow service for your transactions on Telegram.
Avoid scams, your funds are safeguarded throughout your deals. If you run into any issues, simply type /dispute and an arbitrator will join the group chat within 24 hours.

🏧 ESCROW FEE:
1.0% for P2P and 1.0% for OTC Flat

🌐 (UPDATES) - (VOUCHERS) ✅

💬 Proceed with /escrow (to start with a new escrow)

⚠️ IMPORTANT - Make sure coin is same of Buyer and Seller else you may loose your coin.

💡 Type /menu to summon a menu with all bots features"""

ESCROW_TYPE_TEXT = "Please select your escrow type from below."

GROUP_WELCOME_PIN = """📍 Hey there traders! Welcome to our escrow service."""

GROUP_START_TEXT = """📍 Hey there traders! Welcome to our escrow service.
✅ Please start with /dd command and fill the DealInfo Form"""


# ==================== COMMAND HANDLERS ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.add_user(user.id, user.username or user.first_name)
    
    # Send welcome message
    await update.message.reply_text(WELCOME_TEXT, reply_markup=welcome_keyboard())
    
    # THEN send new message with escrow type selection (as per screenshots)
    await update.message.reply_text(ESCROW_TYPE_TEXT, reply_markup=escrow_type_keyboard())


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_TEXT, reply_markup=welcome_keyboard())
    await update.message.reply_text(ESCROW_TYPE_TEXT, reply_markup=escrow_type_keyboard())


async def escrow_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /escrow command - Creates escrow group.
    NOTE: Bot API cannot create groups. User must manually:
    1. Create a group
    2. Add this bot as admin
    3. Send /start in the group
    """
    user = update.effective_user
    
    if update.effective_chat.type == 'private':
        await update.message.reply_text(
            "🤖 To start an escrow:\n\n"
            "1️⃣ Create a new group\n"
            "2️⃣ Add me (@PagaLEscrowBot) as admin\n"
            "3️⃣ Send /start in that group\n\n"
            "Or click P2P below:",
            reply_markup=escrow_type_keyboard()
        )
    else:
        group_id = update.effective_chat.id
        creator = user
        
        # Check if escrow already exists
        existing = db.get_escrow_by_group(group_id)
        if existing:
            await update.message.reply_text("❌ An escrow already exists in this group!")
            return
        
        escrow_id = db.create_escrow(group_id, creator.id, creator.username or creator.first_name)
        
        # Generate invite link
        try:
            link = await context.bot.create_chat_invite_link(
                group_id,
                member_limit=2,
                name=f"Escrow-{escrow_id}"
            )
            db.update_escrow(escrow_id, invite_link=link.invite_link)
        except Exception as e:
            logger.error(f"Invite link error: {e}")
            link = None
        
        await update.message.reply_text(
            f"📍 <b>Escrow Group Created</b>\n\n"
            f"Creator: {creator.first_name}\n\n"
            f"Join this escrow group and share the link with the buyer and seller.\n\n"
            f"{'<a href=\"' + link.invite_link + '\">' + link.invite_link + '</a>' if link else 'Link unavailable'}\n\n"
            f"⚠️ <b>Note:</b> This link is for 2 members only—third parties are not allowed to join.",
            parse_mode='HTML',
            disable_web_page_preview=True
        )
        
        # Pin welcome message
        pin_msg = await context.bot.send_message(group_id, GROUP_WELCOME_PIN)
        await context.bot.pin_chat_message(group_id, pin_msg.message_id)
        
        # Send start instruction
        await context.bot.send_message(
            group_id,
            GROUP_START_TEXT
        )


async def dd_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Deal Details command"""
    if update.effective_chat.type == 'private':
        await update.message.reply_text("❌ This command only works in escrow groups!")
        return
    
    group_id = update.effective_chat.id
    escrow = db.get_escrow_by_group(group_id)
    if not escrow:
        await update.message.reply_text("❌ No active escrow in this group!")
        return
    
    user = update.effective_user
    db.update_escrow(escrow['escrow_id'], status='awaiting_dd')
    
    # Change group name to include escrow ID (Screenshot #5)
    try:
        new_title = f"P2P Escrow By PAGAL Bot ({escrow['escrow_id']})"
        await context.bot.set_chat_title(group_id, new_title)
    except Exception as e:
        logger.error(f"Title change error: {e}")
    
    text = f"""Hello there,
Kindly tell deal details i.e.

Quantity -
Rate -
Conditions (if any) -

Remember without it disputes wouldn't be resolved. Once filled proceed with Specifications of the seller or buyer with /seller or /buyer [CRYPTO ADDRESS]"""
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("How To Use Bot ❓", url="https://t.me/PagaLEscrowBot")]
    ]))


async def buyer_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == 'private':
        return
    
    group_id = update.effective_chat.id
    escrow = db.get_escrow_by_group(group_id)
    if not escrow:
        return
    
    args = context.args
    if not args:
        await update.message.reply_text("❌ Usage: /buyer [CRYPTO ADDRESS]")
        return
    
    wallet = args[0]
    user = update.effective_user
    
    db.set_buyer(escrow['escrow_id'], user.id, user.username or user.first_name, wallet)
    
    text = f"""📍 ESCROW-ROLE DECLARATION

⚡ BUYER @{user.username or user.first_name} | Userid: [{user.id}]

✅ BUYER WALLET
{wallet}

Note: If you don't see any address, then your address will used from saved addresses after selecting token and chain for the current escrow."""
    
    await update.message.reply_text(text)
    await update.message.reply_text("Please set seller using /seller [DEPOSIT ADDRESS]")


async def seller_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == 'private':
        return
    
    group_id = update.effective_chat.id
    escrow = db.get_escrow_by_group(group_id)
    if not escrow:
        return
    
    args = context.args
    if not args:
        await update.message.reply_text("❌ Usage: /seller [DEPOSIT ADDRESS]")
        return
    
    wallet = args[0]
    user = update.effective_user
    
    db.set_seller(escrow['escrow_id'], user.id, user.username or user.first_name, wallet)
    
    text = f"""📍 ESCROW-ROLE DECLARATION

⚡ SELLER @{user.username or user.first_name} | Userid: [{user.id}]

✅ SELLER WALLET
{wallet}

Note: If you don't see any address, then your address will used from saved addresses after selecting token and chain for the current escrow."""
    
    await update.message.reply_text(text)
    await update.message.reply_text("Use /token to Choose crypto.")


async def token_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == 'private':
        return
    
    group_id = update.effective_chat.id
    escrow = db.get_escrow_by_group(group_id)
    if not escrow or escrow['status'] != 'awaiting_token':
        return
    
    await update.message.reply_text("choose token from the list below", reply_markup=token_keyboard())


async def deposit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == 'private':
        return
    
    group_id = update.effective_chat.id
    escrow = db.get_escrow_by_group(group_id)
    if not escrow or escrow['status'] != 'active':
        await update.message.reply_text("❌ Escrow not active yet!")
        return
    
    await update.message.reply_text("Requesting a deposit address for you, please wait...")
    
    # Generate random escrow address (REPLACE with real wallet API)
    fake_address = '0x' + ''.join(random.choices(string.hexdigits.lower(), k=40))
    db.set_escrow_address(escrow['escrow_id'], fake_address)
    
    # Calculate fee
    fee = ESCROW_FEE_DEFAULT
    
    text = f"""📍 TRANSACTION INFORMATION [{escrow['escrow_id']}]

⚡ SELLER
@{escrow['seller_username']} | [{escrow['seller_id']}]
{escrow['seller_wallet'][:20]}...
[{escrow['token']}][{escrow['network']}]

⚡ BUYER
@{escrow['buyer_username']} | [{escrow['buyer_id']}]
{escrow['buyer_wallet'][:20]}...
[{escrow['token']}][{escrow['network']}]

🟢 ESCROW ADDRESS
{fake_address} [{escrow['token']}][{escrow['network']}]

Seller [@{escrow['seller_username']}] Will Pay on the Escrow Address, And Click On Check Payment.

Amount Received: 0.00000 [0.00$]

⏰ Trade Start Time: {escrow['trade_start_time']}
⏰ Address Reset In: {ADDRESS_EXPIRY_MINUTES}.00 Min

📝 Note: Address will reset after the given time, so make sure to deposit in the bot before the address expires.
Useful commands:
📝 /release = Will Release The Funds To Buyer.
📝 /refund = Will Refund The Funds To Seller.

Remember, once commands are used payment will be released, there is no revert!"""
    
    msg = await update.message.reply_text(text, reply_markup=check_payment_keyboard())
    
    # Pin this message
    await context.bot.pin_chat_message(group_id, msg.message_id)
    
    # Send fee notice
    await update.message.reply_text(
        f"Your Fee is {fee}% as both buyer and seller are not using @PagaLEscrowBot in your bio."
    )


async def release_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == 'private':
        return
    
    group_id = update.effective_chat.id
    escrow = db.get_escrow_by_group(group_id)
    if not escrow:
        return
    
    db.update_escrow(escrow['escrow_id'], status='completed')
    await update.message.reply_text(
        f"✅ Funds released to buyer @{escrow['buyer_username']}!\n\n"
        f"Transaction complete. Thank you for using PAGAL Escrow Bot 🤖"
    )


async def refund_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == 'private':
        return
    
    group_id = update.effective_chat.id
    escrow = db.get_escrow_by_group(group_id)
    if not escrow:
        return
    
    db.update_escrow(escrow['escrow_id'], status='refunded')
    await update.message.reply_text(
        f"✅ Funds refunded to seller @{escrow['seller_username']}!\n\n"
        f"Transaction refunded. Thank you for using PAGAL Escrow Bot 🤖"
    )


async def dispute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        "🚨 Dispute raised!\n\n"
        "An arbitrator will join the group chat within 24 hours.\n"
        "Please do not send funds until the dispute is resolved."
    )
    # Notify admins
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                admin_id,
                f"🚨 DISPUTE ALERT\n\n"
                f"User: @{user.username} [{user.id}]\n"
                f"Chat: {update.effective_chat.title}\n"
                f"Chat ID: {update.effective_chat.id}"
            )
        except:
            pass


# ==================== CALLBACK HANDLERS ====================
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user = update.effective_user
    
    if data == 'commands_list':
        text = """📋 COMMANDS LIST 🤖

/start - Start the bot
/menu - Show main menu
/escrow - Create new escrow
/dd - Fill Deal Details
/buyer [ADDRESS] - Set buyer wallet
/seller [ADDRESS] - Set seller wallet
/token - Choose cryptocurrency
/deposit - Generate deposit address
/release - Release funds to buyer
/refund - Refund funds to seller
/dispute - Raise a dispute"""
        await query.message.reply_text(text)
    
    elif data == 'p2p':
        # Auto-run escrow flow
        await query.message.reply_text("Creating a safe trading place for you, please wait...")
        # In real implementation with Telethon, group would be created here
        await query.message.reply_text(
            "📍 To create a P2P escrow:\n\n"
            "1️⃣ Create a new group\n"
            "2️⃣ Add me as admin\n"
            "3️⃣ Send /escrow in the group"
        )
    
    elif data == 'product_deal':
        await query.message.reply_text("🛍️ Product Deal feature coming soon!")
    
    elif data.startswith('token_'):
        token = data.split('_')[1].upper()
        group_id = update.effective_chat.id
        escrow = db.get_escrow_by_group(group_id)
        if escrow:
            db.set_token(escrow['escrow_id'], token)
            await query.message.reply_text(
                f"📍 ESCROW-CRYPTO DECLARATION\n\n"
                f"✅ CRYPTO\n{token}\n\n"
                f"choose network from the list below for {token}",
                reply_markup=network_keyboard(token)
            )
    
    elif data.startswith('net_'):
        network_map = {
            'net_bsc': 'BSC',
            'net_tron': 'TRON',
            'net_btc': 'BTC',
            'net_ltc': 'LTC'
        }
        network = network_map.get(data, 'BSC')
        group_id = update.effective_chat.id
        escrow = db.get_escrow_by_group(group_id)
        if escrow:
            db.set_network(escrow['escrow_id'], network)
            
            # Get updated escrow
            escrow = db.get_escrow_by_id(escrow['escrow_id'])
            
            text = f"""📍 ESCROW DECLARATION

⚡ Seller @{escrow['seller_username']} | Userid: [{escrow['seller_id']}]

✅ {escrow['token']} CRYPTO
✅ {network} NETWORK"""
            
            await query.message.reply_text(text, reply_markup=accept_reject_keyboard())
    
    elif data == 'accept_escrow':
        group_id = update.effective_chat.id
        escrow = db.get_escrow_by_group(group_id)
        if not escrow:
            return
        
        db.accept_escrow(escrow['escrow_id'])
        escrow = db.get_escrow_by_id(escrow['escrow_id'])
        
        # Send full declaration
        text = f"""📍 ESCROW DECLARATION

⚡ Buyer @{escrow['buyer_username']} | Userid: [{escrow['buyer_id']}]
⚡ Seller @{escrow['seller_username']} | Userid: [{escrow['seller_id']}]

✅ {escrow['token']} CRYPTO
✅ {escrow['network']} NETWORK"""
        
        await query.message.reply_text(text)
        
        # Transaction Information
        trans_text = f"""📍 TRANSACTION INFORMATION [{escrow['escrow_id']}]

⚡ SELLER
@{escrow['seller_username']} | [{escrow['seller_id']}]
{escrow['seller_wallet']}[{escrow['token']}][{escrow['network']}]

⚡ BUYER
@{escrow['buyer_username']} | [{escrow['buyer_id']}]
{escrow['buyer_wallet']}[{escrow['token']}][{escrow['network']}]

⏰ Trade Start Time: {escrow['trade_start_time']}

⚠️ IMPORTANT: Make sure to finalise and agree each-others terms before depositing.

📝 Please use /deposit command to generate a deposit address for your trade."""
        
        await query.message.reply_text(trans_text)
        
        # Change group photo (Screenshot #12)
        try:
            photo_path = generate_group_photo(
                escrow['buyer_username'] or 'buyer',
                escrow['seller_username'] or 'seller'
            )
            if photo_path and os.path.exists(photo_path):
                with open(photo_path, 'rb') as f:
                    await context.bot.set_chat_photo(group_id, photo=f)
        except Exception as e:
            logger.error(f"Photo change error: {e}")
        
        # Fee notice
        fee = ESCROW_FEE_DEFAULT
        await query.message.reply_text(
            f"Your Fee is {fee}% as both buyer and seller are not using @PagaLEscrowBot in your bio."
        )
    
    elif data == 'reject_escrow':
        await query.message.reply_text("❌ Escrow rejected. Start over with /escrow")
    
    elif data == 'check_payment':
        await query.message.reply_text("🔍 Checking payment status... (Demo: No payment detected yet)")


# ==================== AUTO-CORRECTION MIDDLEWARE ====================
async def auto_correct_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Middleware-like handler for auto-correcting commands"""
    if not update.message or not update.message.text:
        return
    
    text = update.message.text
    corrected, cmd = auto_correct_command(text)
    
    if corrected:
        await update.message.reply_text(
            f"🤔 Did you mean <code>{corrected}</code>?\n\n"
            f"Running <b>/{cmd}</b> for you...",
            parse_mode='HTML'
        )
        # Simulate the corrected command
        if cmd == 'escrow':
            await escrow_command(update, context)
        elif cmd == 'dd':
            await dd_command(update, context)
        elif cmd == 'buyer':
            context.args = corrected.split()[1:]
            await buyer_command(update, context)
        elif cmd == 'seller':
            context.args = corrected.split()[1:]
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
    
    # Set bot commands menu
    application.bot.set_my_commands([
        BotCommand("start", "Start the bot"),
        BotCommand("menu", "Show menu"),
        BotCommand("escrow", "Create escrow"),
        BotCommand("dd", "Deal details"),
        BotCommand("buyer", "Set buyer address"),
        BotCommand("seller", "Set seller address"),
        BotCommand("token", "Choose crypto"),
        BotCommand("deposit", "Get deposit address"),
        BotCommand("release", "Release funds"),
        BotCommand("refund", "Refund funds"),
        BotCommand("dispute", "Raise dispute")
    ])
    
    print("🤖 PAGAL Escrow Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
