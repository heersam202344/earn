import asyncio
import os
import random
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandObject
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from aiogram.client.default import DefaultBotProperties

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.channels import (
    CreateChannelRequest,
    InviteToChannelRequest,
    EditTitleRequest,
    EditPhotoRequest,
)
from telethon.tl.functions.messages import ExportChatInviteRequest
from telethon.tl.types import InputChatUploadedPhoto


# ============================================================
# ENVIRONMENT
# ============================================================

BOT_TOKEN = os.environ["BOT_TOKEN"]

ADMIN_IDS = {
    int(x.strip())
    for x in os.getenv("ADMIN_IDS", "").split(",")
    if x.strip()
}

BOT_USERNAME = os.getenv("BOT_USERNAME", "PegeLEscrowBot").lstrip("@")

# All start/menu redirect buttons from the screenshots point to
# the same destination.
PAGAL_WORLD_URL = os.getenv(
    "PAGAL_WORLD_URL",
    "https://t.me/PagalWorlddhehe",
)

FEE_PERCENT = os.getenv("FEE_PERCENT", "1.0")

GROUP_INITIAL_PHOTO = os.getenv("GROUP_INITIAL_PHOTO", "")
GROUP_TRANSACTION_PHOTO = os.getenv("GROUP_TRANSACTION_PHOTO", "")

PHOTO_TEMPLATE = os.getenv(
    "PHOTO_TEMPLATE",
    "assets/escrow_photo_template.png",
)

DB = Path("data/escrow.db")
DB.parent.mkdir(parents=True, exist_ok=True)


# ============================================================
# DATABASE
# ============================================================

conn = sqlite3.connect(DB, check_same_thread=False)
conn.row_factory = sqlite3.Row

conn.execute(
    """
    CREATE TABLE IF NOT EXISTS escrows (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trade_code TEXT UNIQUE,
        creator_id INTEGER NOT NULL,
        creator_name TEXT,
        group_id INTEGER,
        group_title TEXT,
        invite_link TEXT,

        buyer_id INTEGER,
        buyer_username TEXT,
        buyer_name TEXT,
        buyer_wallet TEXT,

        seller_id INTEGER,
        seller_username TEXT,
        seller_name TEXT,
        seller_wallet TEXT,

        crypto TEXT,
        network TEXT,

        status TEXT DEFAULT 'created',
        created_at TEXT NOT NULL,

        deposit_address TEXT,
        amount REAL DEFAULT 0,
        fee_percent TEXT DEFAULT '1.0'
    )
    """
)

# Upgrade old databases without destroying existing data.
existing_columns = {
    row["name"]
    for row in conn.execute("PRAGMA table_info(escrows)").fetchall()
}

for column, definition in [
    ("buyer_name", "TEXT"),
    ("seller_name", "TEXT"),
]:
    if column not in existing_columns:
        conn.execute(
            f"ALTER TABLE escrows ADD COLUMN {column} {definition}"
        )

conn.commit()


dp = Dispatcher()


# ============================================================
# TEXT / FORMAT HELPERS
# ============================================================

WELCOME = """💫 @PagaLEscrowBot 💫
Your Trustworthy Telegram Escrow Service

Welcome to @PagaLEscrowBot. This bot provides a reliable escrow service for your transactions on Telegram.
Avoid scams, your funds are safeguarded throughout your deals. If you run into any issues, simply type /dispute and an arbitrator will join the group chat within 24 hours.

💸 <b>ESCROW FEE:</b>
1.0% for P2P and 1.0% for OTC Flat

🌐 (<a href="{world_url}">UPDATES</a>) - (<a href="{world_url}">VOUCHES</a>) ✅

💬 Proceed with /escrow (to start with a new escrow)

⚠️ <b>IMPORTANT</b> - Make sure coin is same of Buyer and Seller else you may loose your coin.

💡 Type /menu to summon a menu with all bots features"""


def world_button(text: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text=text,
        url=PAGAL_WORLD_URL,
    )


def start_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="P2P",
                    callback_data="type_p2p",
                ),
                InlineKeyboardButton(
                    text="Product Deal",
                    callback_data="type_product",
                ),
            ],
            [
                world_button("COMMANDS LIST 🤖"),
            ],
            [
                world_button("☎️ CONTACT"),
            ],
            [
                world_button("Updates 🔄"),
                world_button("Vouches ✔️"),
            ],
            [
                world_button("WHAT IS ESCROW ?"),
                world_button("Instructions 👩‍🏫"),
            ],
            [
                world_button("Terms 📝"),
            ],
            [
                world_button("Invites 👤"),
            ],
        ]
    )


def menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                world_button("COMMANDS LIST 🤖"),
            ],
            [
                world_button("☎️ CONTACT"),
            ],
            [
                world_button("Updates 🔄"),
                world_button("Vouches ✔️"),
            ],
            [
                world_button("WHAT IS ESCROW ?"),
                world_button("Instructions 👩‍🏫"),
            ],
            [
                world_button("Terms 📝"),
            ],
            [
                world_button("Invites 👤"),
            ],
        ]
    )


def escrow_type_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="P2P",
                    callback_data="type_p2p",
                ),
                InlineKeyboardButton(
                    text="Product Deal",
                    callback_data="type_product",
                ),
            ]
        ]
    )


def token_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="LTC",
                    callback_data="token_ltc",
                ),
                InlineKeyboardButton(
                    text="BTC",
                    callback_data="token_btc",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="USDT",
                    callback_data="token_usdt",
                ),
            ],
        ]
    )


def network_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="BSC[BEP20]",
                    callback_data="net_bsc",
                ),
                InlineKeyboardButton(
                    text="TRON[TRC20]",
                    callback_data="net_tron",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Back ⬅️",
                    callback_data="back_token",
                ),
            ],
        ]
    )


def accept_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Accept ✅",
                    callback_data="accept_trade",
                ),
                InlineKeyboardButton(
                    text="Reject ❌",
                    callback_data="reject_trade",
                ),
            ]
        ]
    )


def deposit_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Check Payment",
                    callback_data="check_payment",
                ),
            ]
        ]
    )


def user_display_name(user) -> str:
    """
    Screenshot flow uses the creator's display/full name,
    not @username.
    """
    parts = [
        getattr(user, "first_name", None),
        getattr(user, "last_name", None),
    ]
    name = " ".join(x for x in parts if x).strip()
    return name or getattr(user, "username", None) or "User"


def username_only(user) -> str:
    return getattr(user, "username", None) or user_display_name(user)


# ============================================================
# DATABASE HELPERS
# ============================================================

def get_escrow(eid):
    return conn.execute(
        "SELECT * FROM escrows WHERE id=?",
        (eid,),
    ).fetchone()


def update_eid(eid, **kwargs):
    if not kwargs:
        return

    allowed = {
        "trade_code",
        "creator_id",
        "creator_name",
        "group_id",
        "group_title",
        "invite_link",
        "buyer_id",
        "buyer_username",
        "buyer_name",
        "buyer_wallet",
        "seller_id",
        "seller_username",
        "seller_name",
        "seller_wallet",
        "crypto",
        "network",
        "status",
        "created_at",
        "deposit_address",
        "amount",
        "fee_percent",
    }

    kwargs = {
        key: value
        for key, value in kwargs.items()
        if key in allowed
    }

    if not kwargs:
        return

    cols = ", ".join(f"{key}=?" for key in kwargs)
    vals = list(kwargs.values()) + [eid]

    conn.execute(
        f"UPDATE escrows SET {cols} WHERE id=?",
        vals,
    )
    conn.commit()


def latest_for_user(uid):
    return conn.execute(
        """
        SELECT *
        FROM escrows
        WHERE creator_id=?
        ORDER BY id DESC
        LIMIT 1
        """,
        (uid,),
    ).fetchone()


def latest_for_chat(chat_id):
    return conn.execute(
        """
        SELECT *
        FROM escrows
        WHERE group_id=?
        ORDER BY id DESC
        LIMIT 1
        """,
        (chat_id,),
    ).fetchone()


def latest_active_for_user(uid):
    return conn.execute(
        """
        SELECT *
        FROM escrows
        WHERE
            (creator_id=? OR buyer_id=? OR seller_id=?)
            AND status NOT IN ('rejected', 'closed')
        ORDER BY id DESC
        LIMIT 1
        """,
        (uid, uid, uid),
    ).fetchone()


def latest_escrow_for_message(m: Message):
    return (
        latest_for_chat(m.chat.id)
        or latest_active_for_user(m.from_user.id)
    )


# ============================================================
# ESCROW MESSAGES
# ============================================================

def tx_decl(e):
    return f"""📌 <b>ESCROW DECLARATION</b>

⚡ Buyer @{e["buyer_username"] or "unknown"} | Userid: [{e["buyer_id"] or "-"}]
⚡ Seller @{e["seller_username"] or "unknown"} | Userid: [{e["seller_id"] or "-"}]

<b>✅ {e["crypto"] or "CRYPTO"} CRYPTO</b>
<b>✅ {e["network"] or "NETWORK"} NETWORK</b>"""


def transaction_info(e):
    return f"""📌 <b>TRANSACTION INFORMATION [{e["trade_code"]}]</b>

⚡ <b>SELLER</b>
@{e["seller_username"] or "unknown"} | [{e["seller_id"] or "-"}]
<code>{e["seller_wallet"] or "-"}</code> [{e["crypto"] or "-"}]
[{e["network"] or "-"}]

⚡ <b>BUYER</b>
@{e["buyer_username"] or "unknown"} | [{e["buyer_id"] or "-"}]
<code>{e["buyer_wallet"] or "-"}</code> [{e["crypto"] or "-"}]
[{e["network"] or "-"}]

⏰ <b>Trade Start Time:</b> {e["created_at"]}

⚠️ <b>IMPORTANT:</b> Make sure to finalise and agree each-other's terms before depositing.

📄 Please use /deposit command to generate a deposit address for your trade."""


def configured_deposit_address(e):
    key = "DEPOSIT_ADDRESS_" + (e["crypto"] or "").upper()

    if e["crypto"] == "USDT":
        key += "_" + (
            e["network"] or ""
        ).upper().replace("TRON", "TRC20")

    return os.getenv(key, "YOUR_DEPOSIT_ADDRESS")


# ============================================================
# TELETHON
# ============================================================

async def telethon_client():
    api_id = os.getenv("API_ID")
    api_hash = os.getenv("API_HASH")
    session = os.getenv("STRING_SESSION")

    if not api_id or not api_hash or not session:
        return None

    try:
        client = TelegramClient(
            StringSession(session),
            int(api_id),
            api_hash,
            connection_retries=3,
            request_retries=3,
            timeout=30,
        )
        await client.connect()

        if not await client.is_user_authorized():
            print("Telethon STRING_SESSION is not authorized as a user session.")
            await client.disconnect()
            return None

        return client
    except Exception as exc:
        print("telethon_client ERROR:", repr(exc))
        return None


async def set_group_photo(eid: int, path: str):
    if not path or not os.path.exists(path):
        return False

    client = await telethon_client()
    if not client:
        return False

    try:
        e = get_escrow(eid)
        if not e or not e["group_id"]:
            return False

        entity = await client.get_entity(e["group_id"])
        uploaded = await client.upload_file(path)

        await client(
            EditPhotoRequest(
                entity,
                InputChatUploadedPhoto(file=uploaded),
            )
        )

        return True

    except Exception as exc:
        print("set_group_photo:", exc)
        return False

    finally:
        await client.disconnect()


async def edit_group_title(eid: int, title: str):
    client = await telethon_client()
    if not client:
        return False

    try:
        e = get_escrow(eid)
        if not e or not e["group_id"]:
            return False

        entity = await client.get_entity(e["group_id"])

        await client(
            EditTitleRequest(
                entity,
                title,
            )
        )

        update_eid(eid, group_title=title)
        return True

    except Exception as exc:
        print("edit_group_title:", exc)
        return False

    finally:
        await client.disconnect()


async def create_private_group(eid):
    """
    Creates the private megagroup with the Telethon USER session.
    The Bot API token cannot create Telegram groups; API_ID/API_HASH/
    STRING_SESSION must belong to an authorized Telegram USER account.
    """
    client = await telethon_client()
    if not client:
        return {"ok": False, "error": "Telethon user session is not authorized."}

    try:
        # 1) Create the actual private megagroup.
        result = await client(
            CreateChannelRequest(
                title="P2P Escrow By PAGAL Bot",
                about="📌 Hey there traders! Welcome to our escrow service.",
                megagroup=True,
            )
        )

        if not result.chats:
            return {"ok": False, "error": "Telegram did not return the created group."}

        chat = result.chats[0]
        entity = await client.get_entity(chat)

        # 2) Save group information immediately.
        update_eid(
            eid,
            group_id=chat.id,
            group_title="P2P Escrow By PAGAL Bot",
        )

        # 3) Generate the private invite link.
        inv = await client(
            ExportChatInviteRequest(entity)
        )
        link = getattr(inv, "link", None)

        if link:
            update_eid(eid, invite_link=link)

        # 4) Add the bot account to the group.
        # BOT_USERNAME must be the bot's @username, without @.
        if BOT_USERNAME:
            try:
                bot_entity = await client.get_entity(BOT_USERNAME)

                await client(
                    InviteToChannelRequest(
                        entity,
                        [bot_entity],
                    )
                )
            except Exception as exc:
                # Group is still successfully created even if the bot
                # could not be invited. Keep the real error for logs.
                print("BOT INVITE ERROR:", repr(exc))

        # 5) Set initial group photo.
        if GROUP_INITIAL_PHOTO:
            try:
                if os.path.exists(GROUP_INITIAL_PHOTO):
                    uploaded = await client.upload_file(
                        GROUP_INITIAL_PHOTO
                    )
                    await client(
                        EditPhotoRequest(
                            entity,
                            InputChatUploadedPhoto(file=uploaded),
                        )
                    )
                else:
                    print(
                        "GROUP_INITIAL_PHOTO does not exist:",
                        GROUP_INITIAL_PHOTO,
                    )
            except Exception as exc:
                print("INITIAL PHOTO ERROR:", repr(exc))

        return {
            "ok": True,
            "link": link,
            "chat_id": chat.id,
        }

    except Exception as exc:
        # Print the actual Telegram error instead of silently returning None.
        print("CREATE GROUP ERROR:", repr(exc))
        return {
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
        }

    finally:
        await client.disconnect()


async def rename_on_dd(eid):
    e = get_escrow(eid)
    if e and e["group_id"]:
        await edit_group_title(
            eid,
            f"P2P Escrow By PAGAL Bot ({e['trade_code']})",
        )


# ============================================================
# TRANSACTION PHOTO
# ============================================================

def load_font(size, bold=False):
    candidates = []

    if bold:
        candidates.extend([
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
        ])
    else:
        candidates.extend([
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        ])

    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)

    return ImageFont.load_default()


def make_transaction_photo(e):
    """
    Generates the transaction group photo.
    The template controls the logo/branding; text is overlaid
    with consistent bold/normal typography.
    """

    out = Path("data") / f"escrow_photo_{e['id']}.jpg"

    try:
        canvas = Image.new("RGB", (640, 640), (4, 5, 6))

        # Use supplied screenshot/template if available.
        if os.path.exists(PHOTO_TEMPLATE):
            template = Image.open(PHOTO_TEMPLATE).convert("RGB")
            template.thumbnail((600, 600))

            x = (640 - template.width) // 2
            y = 0

            canvas.paste(template, (x, y))

        draw = ImageDraw.Draw(canvas)

        buyer = (
            e["buyer_username"]
            or e["buyer_name"]
            or str(e["buyer_id"] or "unknown")
        )

        seller = (
            e["seller_username"]
            or e["seller_name"]
            or str(e["seller_id"] or "unknown")
        )

        bold = load_font(27, bold=True)

        # The text area is deliberately kept separate from the
        # template/logo so the branding remains clean.
        draw.text(
            (70, 475),
            f"💰 BUYER:  @{buyer}",
            font=bold,
            fill="white",
        )

        draw.text(
            (70, 525),
            f"💰 SELLER: @{seller}",
            font=bold,
            fill="white",
        )

        canvas.save(
            out,
            quality=95,
            optimize=True,
        )

        return str(out)

    except Exception as exc:
        print("make_transaction_photo:", exc)
        return None


async def transaction_photo(eid):
    e = get_escrow(eid)
    if not e:
        return

    path = (
        GROUP_TRANSACTION_PHOTO
        or make_transaction_photo(e)
    )

    if path:
        await set_group_photo(eid, path)


# ============================================================
# START / MENU
# ============================================================

@dp.message(Command("start"))
async def start(m: Message):
    # Screenshot flow: start message + escrow selector immediately below.
    await m.answer(
        WELCOME.format(
            world_url=PAGAL_WORLD_URL
        ),
        reply_markup=start_kb(),
        disable_web_page_preview=True,
    )

    await m.answer(
        "Please select your escrow type from below.",
        reply_markup=escrow_type_kb(),
    )


@dp.message(Command("menu"))
async def menu(m: Message):
    await m.answer(
        "💡 <b>Commands / Menu</b>",
        reply_markup=menu_kb(),
    )


@dp.message(Command("escrow"))
async def escrow(m: Message):
    await m.answer(
        "Please select your escrow type from below.",
        reply_markup=escrow_type_kb(),
    )


# ============================================================
# ESCROW TYPE
# ============================================================

@dp.callback_query(F.data.startswith("type_"))
async def type_callback(c: CallbackQuery):
    if c.data == "type_product":
        await c.message.answer("Product Deal selected.")
        await c.answer()
        return

    # Prevent the Telegram callback spinner while the user-session
    # creates the group.
    await c.answer()

    # Create the database record first.
    eid = await create_escrow(
        c.from_user.id,
        user_display_name(c.from_user),
    )

    # IMPORTANT: edit the selector message instead of sending another
    # "creating..." message. This matches the screenshot-style flow.
    try:
        await c.message.edit_text(
            "Creating a safe trading place for you, please wait..."
        )
    except Exception as exc:
        print("EDIT CREATE MESSAGE ERROR:", repr(exc))

    result = await create_private_group(eid)

    if result.get("ok"):
        e = get_escrow(eid)
        link = result.get("link")

        # Edit the same message again after the group has been created.
        # No extra "Escrow Group Created" message is sent.
        if link:
            text = (
                f"<b>Escrow Group Created</b>\n\n"
                f"Creator: {e['creator_name']}\n\n"
                f"Join this escrow group and share the link with the buyer and seller.\n\n"
                f"<code>{link}</code>\n\n"
                f"⚠️ Note: This link is for 2 members only—third parties are not allowed to join."
            )
        else:
            text = (
                f"<b>Escrow Group Created</b>\n\n"
                f"Creator: {e['creator_name']}\n\n"
                "The private group was created, but Telegram did not return "
                "an invite link."
            )

        try:
            await c.message.edit_text(
                text,
                disable_web_page_preview=True,
            )
        except Exception as exc:
            print("EDIT GROUP CREATED MESSAGE ERROR:", repr(exc))
            # Only fall back if Telegram refuses the edit.
            await c.message.answer(
                text,
                disable_web_page_preview=True,
            )

    else:
        error = result.get("error", "Unknown Telethon error.")

        # Show the real error so configuration/permissions problems
        # can be diagnosed instead of displaying a generic message.
        try:
            await c.message.edit_text(
                "<b>Escrow group could not be created.</b>\n\n"
                "Telethon error:\n"
                f"<code>{error}</code>\n\n"
                "Make sure API_ID, API_HASH and STRING_SESSION belong "
                "to an authorized Telegram USER account."
            )
        except Exception as exc:
            print("EDIT GROUP ERROR MESSAGE ERROR:", repr(exc))
            await c.message.answer(
                "<b>Escrow group could not be created.</b>\n\n"
                f"<code>{error}</code>"
            )


# ============================================================
# TOKEN
# ============================================================

async def select_token(c: CallbackQuery, crypto: str):
    e = (
        latest_for_chat(c.message.chat.id)
        or latest_active_for_user(c.from_user.id)
    )

    if not e:
        await c.answer(
            "No escrow found.",
            show_alert=True,
        )
        return

    update_eid(
        e["id"],
        crypto=crypto,
    )

    if crypto == "USDT":
        await c.message.edit_text(
            "📌 <b>ESCROW-CRYPTO DECLARATION</b>\n\n"
            "✅ <b>CRYPTO</b>\n"
            "USDT\n\n"
            "<b>choose network from the list below for USDT</b>",
            reply_markup=network_kb(),
        )
    else:
        await finish_token(c, None)

    await c.answer()


async def finish_token(c: CallbackQuery, network):
    e = (
        latest_for_chat(c.message.chat.id)
        or latest_active_for_user(c.from_user.id)
    )

    if not e:
        await c.answer(
            "No escrow found.",
            show_alert=True,
        )
        return

    update_eid(
        e["id"],
        network=network,
    )

    e = get_escrow(e["id"])

    await c.message.answer(
        tx_decl(e),
        reply_markup=accept_kb(),
    )

    await c.answer()


@dp.callback_query(F.data == "token_ltc")
async def token_ltc(c: CallbackQuery):
    await select_token(c, "LTC")


@dp.callback_query(F.data == "token_btc")
async def token_btc(c: CallbackQuery):
    await select_token(c, "BTC")


@dp.callback_query(F.data == "token_usdt")
async def token_usdt(c: CallbackQuery):
    await select_token(c, "USDT")


@dp.callback_query(F.data == "net_bsc")
async def net_bsc(c: CallbackQuery):
    await finish_token(c, "BSC")


@dp.callback_query(F.data == "net_tron")
async def net_tron(c: CallbackQuery):
    await finish_token(c, "TRON")


@dp.callback_query(F.data == "back_token")
async def back_token(c: CallbackQuery):
    await c.message.edit_text(
        "<b>choose token from the list below</b>",
        reply_markup=token_kb(),
    )
    await c.answer()


@dp.message(Command("token"))
async def token(m: Message):
    await m.answer(
        "<b>choose token from the list below</b>",
        reply_markup=token_kb(),
    )


# ============================================================
# ACCEPT / REJECT
# ============================================================

@dp.callback_query(F.data == "accept_trade")
async def accept_trade(c: CallbackQuery):
    e = (
        latest_for_chat(c.message.chat.id)
        or latest_active_for_user(c.from_user.id)
    )

    if not e:
        await c.answer(
            "No escrow found.",
            show_alert=True,
        )
        return

    update_eid(
        e["id"],
        status="accepted",
    )

    e = get_escrow(e["id"])

    # Screenshot flow: declaration followed by transaction information.
    await c.message.answer(tx_decl(e))
    await c.message.answer(transaction_info(e))

    # Change group photo to the dynamic transaction photo.
    await transaction_photo(e["id"])

    await c.answer("Accepted")


@dp.callback_query(F.data == "reject_trade")
async def reject_trade(c: CallbackQuery):
    e = (
        latest_for_chat(c.message.chat.id)
        or latest_active_for_user(c.from_user.id)
    )

    if e:
        update_eid(
            e["id"],
            status="rejected",
        )

    await c.message.answer(
        "❌ <b>ESCROW DECLARATION REJECTED</b>"
    )

    await c.answer("Rejected")


# ============================================================
# DD / BUYER / SELLER
# ============================================================

@dp.message(Command("dd"))
async def dd(m: Message):
    e = latest_escrow_for_message(m)

    if e and e["group_id"] == m.chat.id:
        await rename_on_dd(e["id"])

    await m.answer(
        "Hello there,\n"
        "Kindly tell deal details i.e.\n\n"
        "Quantity -\n"
        "Rate -\n"
        "Conditions (if any) -\n\n"
        "Remember without it disputes wouldn’t be resolved. Once filled proceed with\n"
        "Specifications of the seller or buyer with /seller or /buyer [CRYPTO ADDRESS]"
    )


@dp.message(Command("buyer"))
async def buyer(m: Message, command: CommandObject):
    e = latest_escrow_for_message(m)

    if not e:
        await m.answer("No active escrow found.")
        return

    address = (command.args or "").strip()

    if not address:
        await m.answer(
            "Please use /buyer [DEPOSIT ADDRESS]"
        )
        return

    update_eid(
        e["id"],
        buyer_id=m.from_user.id,
        buyer_username=m.from_user.username,
        buyer_name=user_display_name(m.from_user),
        buyer_wallet=address,
    )

    await m.answer(
        f"📌 <b>ESCROW-ROLE DECLARATION</b>\n\n"
        f"⚡ <b>BUYER @{m.from_user.username or m.from_user.first_name} | Userid: [{m.from_user.id}]</b>\n\n"
        f"✅ <b>BUYER WALLET</b>\n"
        f"<code>{address}</code>\n\n"
        "Note: If you don't see any address, then your address will used from saved addresses after selecting token and chain for the current escrow."
    )

    await m.answer(
        "Please set seller using /seller [DEPOSIT ADDRESS]"
    )


@dp.message(Command("seller"))
async def seller(m: Message, command: CommandObject):
    e = latest_escrow_for_message(m)

    if not e:
        await m.answer("No active escrow found.")
        return

    address = (command.args or "").strip()

    if not address:
        await m.answer(
            "Please use /seller [DEPOSIT ADDRESS]"
        )
        return

    update_eid(
        e["id"],
        seller_id=m.from_user.id,
        seller_username=m.from_user.username,
        seller_name=user_display_name(m.from_user),
        seller_wallet=address,
    )

    await m.answer(
        f"📌 <b>ESCROW-ROLE DECLARATION</b>\n\n"
        f"⚡ <b>SELLER @{m.from_user.username or m.from_user.first_name} | Userid: [{m.from_user.id}]</b>\n\n"
        f"✅ <b>SELLER WALLET</b>\n"
        f"<code>{address}</code>\n\n"
        "Note: If you don't see any address, then your address will used from saved addresses after selecting token and chain for the current escrow."
    )

    await m.answer(
        "Use /token to Choose crypto."
    )


# ============================================================
# DEPOSIT
# ============================================================

@dp.message(Command("deposit"))
async def deposit(m: Message):
    e = latest_escrow_for_message(m)

    if not e:
        await m.answer("No active escrow found.")
        return

    address = configured_deposit_address(e)

    update_eid(
        e["id"],
        deposit_address=address,
        status="deposit_ready",
    )

    e = get_escrow(e["id"])

    await m.answer(
        f"📌 <b>TRANSACTION INFORMATION [{e['trade_code']}]</b>\n\n"
        f"⚡ <b>SELLER</b>\n"
        f"@{e['seller_username'] or 'unknown'} | [{e['seller_id'] or '-'}]\n\n"
        f"⚡ <b>BUYER</b>\n"
        f"@{e['buyer_username'] or 'unknown'} | [{e['buyer_id'] or '-'}]\n\n"
        f"🟢 <b>ESCROW ADDRESS</b>\n"
        f"<code>{address}</code> [{e['crypto'] or '-'}]\n"
        f"[{e['network'] or '-'}]\n\n"
        f"Seller [@{e['seller_username'] or 'unknown'}] Will Pay on the Escrow Address, And Click On Check Payment.\n\n"
        "Amount Received: 0.00000 [0.00$]\n\n"
        f"⏰ <b>Trade Start Time:</b> {e['created_at']}\n"
        "⏰ <b>Address Reset In:</b> 20.00 Min\n\n"
        "📄 Note: Address will reset after the given time, so make sure to deposit in the bot before the address expires.\n\n"
        "Useful commands:\n"
        "📄 /release = Will Release The Funds To Buyer.\n\n"
        "📄 /refund = Will Refund The Funds To Seller.\n\n"
        "Remember, once commands are used payment will be released, there is no revert!",
        reply_markup=deposit_kb(),
    )


@dp.callback_query(F.data == "check_payment")
async def check_payment(c: CallbackQuery):
    # Deliberately left as a payment-integration hook.
    await c.message.answer(
        "🔎 <b>CHECK PAYMENT</b>\n"
        "Payment verification is ready for your payment integration."
    )
    await c.answer()


# ============================================================
# RELEASE / REFUND — KEPT SIMPLE, AS REQUESTED
# ============================================================

@dp.message(Command("release"))
async def release(m: Message):
    e = latest_for_chat(m.chat.id)

    if not e:
        await m.answer("No active escrow found.")
        return

    update_eid(
        e["id"],
        status="release_requested",
    )

    await m.answer("<b>Release requested.</b>")


@dp.message(Command("refund"))
async def refund(m: Message):
    e = latest_for_chat(m.chat.id)

    if not e:
        await m.answer("No active escrow found.")
        return

    update_eid(
        e["id"],
        status="refund_requested",
    )

    await m.answer("<b>Refund requested.</b>")


# ============================================================
# DISPUTE
# ============================================================

@dp.message(Command("dispute"))
async def dispute(m: Message):
    await m.answer(
        "⚖️ <b>DISPUTE</b>\n"
        "An arbitrator/support member should review this trade."
    )


# ============================================================
# CREATE ESCROW
# ============================================================

async def create_escrow(uid, creator_name):
    now = datetime.now(
        timezone.utc
    ).strftime("%d/%m/%y %H:%M:%S")

    trade_code = str(
        random.randint(10000000, 99999999)
    )

    while conn.execute(
        "SELECT 1 FROM escrows WHERE trade_code=?",
        (trade_code,),
    ).fetchone():
        trade_code = str(
            random.randint(10000000, 99999999)
        )

    cur = conn.execute(
        """
        INSERT INTO escrows(
            trade_code,
            creator_id,
            creator_name,
            created_at,
            fee_percent
        )
        VALUES(?,?,?,?,?)
        """,
        (
            trade_code,
            uid,
            creator_name,
            now,
            FEE_PERCENT,
        ),
    )

    conn.commit()
    return cur.lastrowid


# ============================================================
# MAIN
# ============================================================

async def main():
    bot = Bot(
        BOT_TOKEN,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML
        ),
    )

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
