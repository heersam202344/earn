import asyncio
import os
from pathlib import Path
from typing import Optional

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandObject
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

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
# CONFIG
# ============================================================

BOT_TOKEN = os.environ["BOT_TOKEN"]

BOT_USERNAME = os.getenv(
    "BOT_USERNAME",
    "PagaLEscrowBot",
).lstrip("@")

# Every external button from the screenshots can point here.
PAGAL_WORLD_URL = os.getenv(
    "PAGAL_WORLD_URL",
    "https://t.me/PagalWorlddhehe",
)

# These are the credentials of the TELEGRAM USER ACCOUNT that
# creates/manages the private escrow groups.
API_ID = os.getenv("API_ID", "")
API_HASH = os.getenv("API_HASH", "")
STRING_SESSION = os.getenv("STRING_SESSION", "").strip()

GROUP_INITIAL_PHOTO = os.getenv("GROUP_INITIAL_PHOTO", "")
GROUP_TRANSACTION_PHOTO = os.getenv("GROUP_TRANSACTION_PHOTO", "")

# Optional custom group photo. If absent, Telegram keeps its default.
PHOTO_TEMPLATE = os.getenv(
    "PHOTO_TEMPLATE",
    "assets/escrow_photo_template.png",
)


# ============================================================
# IN-MEMORY STATE
# ============================================================

# The user explicitly said persistent data is not important.
# Keeping only the current flow makes the code much easier to
# control and avoids stale database records.
escrows = {}
next_trade_id = 10000000


def new_trade(user_id: int, creator_name: str):
    global next_trade_id

    trade_id = str(next_trade_id)
    next_trade_id += 1

    escrows[user_id] = {
        "trade_code": trade_id,
        "creator_id": user_id,
        "creator_name": creator_name,
        "group_id": None,
        "group_link": None,
        "crypto": None,
        "network": None,
        "buyer_id": None,
        "buyer_username": None,
        "buyer_wallet": None,
        "seller_id": None,
        "seller_username": None,
        "seller_wallet": None,
    }

    return escrows[user_id]


def get_trade(user_id: int):
    return escrows.get(user_id)


def display_name(user) -> str:
    first = getattr(user, "first_name", "") or ""
    last = getattr(user, "last_name", "") or ""
    full = f"{first} {last}".strip()

    return (
        full
        or getattr(user, "username", None)
        or "User"
    )


# ============================================================
# KEYBOARDS
# ============================================================

def world_button(text: str):
    return InlineKeyboardButton(
        text=text,
        url=PAGAL_WORLD_URL,
    )


def start_keyboard():
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


def escrow_keyboard():
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


def token_keyboard():
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


def network_keyboard():
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


def accept_keyboard():
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


def deposit_keyboard():
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


# ============================================================
# EXACT MESSAGE TEXT
# ============================================================

WELCOME = """💫 @PagaLEscrowBot 💫
Your Trustworthy Telegram Escrow Service

Welcome to @PagaLEscrowBot. This bot provides a reliable escrow service for your transactions on Telegram.
Avoid scams, your funds are safeguarded throughout your deals. If you run into any issues, simply type /dispute and an arbitrator will join the group chat within 24 hours.

💸 <b>ESCROW FEE:</b>
1.0% for P2P and 1.0% for OTC Flat

🌐 (<a href="{url}">UPDATES</a>) - (<a href="{url}">VOUCHES</a>) ✅

💬 Proceed with /escrow (to start with a new escrow)

⚠️ <b>IMPORTANT</b> - Make sure coin is same of Buyer and Seller else you may loose your coin.

💡 Type /menu to summon a menu with all bots features"""


def declaration(e):
    return f"""📌 <b>ESCROW DECLARATION</b>

⚡ Buyer @{e["buyer_username"] or "unknown"} | Userid: [{e["buyer_id"] or "-"}]
⚡ Seller @{e["seller_username"] or "unknown"} | Userid: [{e["seller_id"] or "-"}]

<b>✅ {e["crypto"] or "CRYPTO"} CRYPTO</b>
<b>✅ {e["network"] or "NETWORK"} NETWORK</b>"""


def transaction_information(e):
    return f"""📌 <b>TRANSACTION INFORMATION [{e["trade_code"]}]</b>

⚡ <b>SELLER</b>
@{e["seller_username"] or "unknown"} | [{e["seller_id"] or "-"}]
<code>{e["seller_wallet"] or "-"}</code> [{e["crypto"] or "-"}]
[{e["network"] or "-"}]

⚡ <b>BUYER</b>
@{e["buyer_username"] or "unknown"} | [{e["buyer_id"] or "-"}]
<code>{e["buyer_wallet"] or "-"}</code> [{e["crypto"] or "-"}]
[{e["network"] or "-"}]

⏰ <b>Trade Start Time:</b> --/--/-- --:--:--

⚠️ <b>IMPORTANT:</b> Make sure to finalise and agree each-other's terms before depositing.

📄 Please use /deposit command to generate a deposit address for your trade."""


# ============================================================
# TELETHON USER ACCOUNT
# ============================================================

async def get_telethon():
    if not API_ID or not API_HASH or not STRING_SESSION:
        raise RuntimeError(
            "API_ID, API_HASH or STRING_SESSION is missing."
        )

    try:
        api_id = int(API_ID)
    except ValueError:
        raise RuntimeError("API_ID must be a number.")

    client = TelegramClient(
        StringSession(STRING_SESSION),
        api_id,
        API_HASH,
    )

    await client.connect()

    if not await client.is_user_authorized():
        await client.disconnect()
        raise RuntimeError(
            "Telethon user session is not authorized. "
            "Create STRING_SESSION using the same Telegram USER account "
            "that should create the escrow groups."
        )

    return client


async def create_escrow_group(e):
    client = await get_telethon()

    try:
        # This group is created by the Telegram USER account represented
        # by STRING_SESSION.
        result = await client(
            CreateChannelRequest(
                title="P2P Escrow By PAGAL Bot",
                about="📌 Hey there traders! Welcome to our escrow service.",
                megagroup=True,
            )
        )

        chat = result.chats[0]
        entity = await client.get_entity(chat)

        # Create a permanent invite link for the private group.
        invite_result = await client(
            ExportChatInviteRequest(
                peer=entity,
            )
        )

        link = getattr(invite_result, "link", None)

        e["group_id"] = chat.id
        e["group_link"] = link

        # Add the Bot account to the group.
        if BOT_USERNAME:
            try:
                bot_entity = await client.get_entity(BOT_USERNAME)

                await client(
                    InviteToChannelRequest(
                        channel=entity,
                        users=[bot_entity],
                    )
                )
            except Exception as exc:
                print("Bot invite warning:", repr(exc))

        # Initial group picture.
        photo = (
            GROUP_INITIAL_PHOTO
            or PHOTO_TEMPLATE
        )

        if photo and os.path.exists(photo):
            try:
                uploaded = await client.upload_file(photo)

                await client(
                    EditPhotoRequest(
                        channel=entity,
                        photo=InputChatUploadedPhoto(
                            file=uploaded
                        ),
                    )
                )
            except Exception as exc:
                print("Group photo warning:", repr(exc))

        return link

    finally:
        await client.disconnect()


async def rename_group(e, title):
    if not e["group_id"]:
        return

    client = await get_telethon()

    try:
        entity = await client.get_entity(e["group_id"])

        await client(
            EditTitleRequest(
                channel=entity,
                title=title,
            )
        )
    finally:
        await client.disconnect()


# ============================================================
# BOT
# ============================================================

dp = Dispatcher()


@dp.message(Command("start"))
async def start(message: Message):
    # First message exactly contains the welcome + button block.
    await message.answer(
        WELCOME.format(url=PAGAL_WORLD_URL),
        reply_markup=start_keyboard(),
        disable_web_page_preview=True,
    )

    # The escrow selector is the next message in the start flow.
    await message.answer(
        "Please select your escrow type from below.",
        reply_markup=escrow_keyboard(),
    )


@dp.message(Command("menu"))
async def menu(message: Message):
    await message.answer(
        "💡 <b>Commands / Menu</b>",
        reply_markup=start_keyboard(),
    )


@dp.message(Command("escrow"))
async def escrow(message: Message):
    await message.answer(
        "Please select your escrow type from below.",
        reply_markup=escrow_keyboard(),
    )


# ============================================================
# P2P / PRODUCT
# ============================================================

async def begin_type(callback: CallbackQuery):
    e = get_trade(callback.from_user.id)

    if not e:
        e = new_trade(
            callback.from_user.id,
            display_name(callback.from_user),
        )

    # SAME MESSAGE: selector -> creating.
    await callback.message.edit_text(
        "Creating a safe trading place for you, please wait..."
    )

    try:
        link = await create_escrow_group(e)

    except Exception as exc:
        # Same message again, so there is no message spam.
        print("Telethon group creation error:", repr(exc))

        await callback.message.edit_text(
            "❌ <b>Escrow group could not be created.</b>\n\n"
            f"<b>Telethon error:</b>\n"
            f"<code>{str(exc)}</code>\n\n"
            "Please check API_ID, API_HASH and STRING_SESSION."
        )
        await callback.answer()
        return

    if not link:
        await callback.message.edit_text(
            "❌ <b>Escrow group could not be created.</b>"
        )
        await callback.answer()
        return

    # SAME MESSAGE: creating -> created.
    await callback.message.edit_text(
        f"<b>Escrow Group Created</b>\n\n"
        f"Creator: {e['creator_name']}\n\n"
        f"Join this escrow group and share the link with the buyer and seller.\n\n"
        f"<code>{link}</code>\n\n"
        f"⚠️ Note: This link is for 2 members only—third parties are not allowed to join.",
        disable_web_page_preview=True,
    )

    await callback.answer()


@dp.callback_query(F.data == "type_p2p")
async def type_p2p(callback: CallbackQuery):
    await begin_type(callback)


@dp.callback_query(F.data == "type_product")
async def type_product(callback: CallbackQuery):
    # Product Deal uses the EXACT SAME message/edit flow.
    await begin_type(callback)


# ============================================================
# DD
# ============================================================

@dp.message(Command("dd"))
async def dd(message: Message):
    e = get_trade(message.from_user.id)

    if e and e["group_id"]:
        try:
            await rename_group(
                e,
                f"P2P Escrow By PAGAL Bot ({e['trade_code']})",
            )
        except Exception as exc:
            print("DD rename warning:", repr(exc))

    await message.answer(
        "Hello there,\n"
        "Kindly tell deal details i.e.\n\n"
        "Quantity -\n"
        "Rate -\n"
        "Conditions (if any) -\n\n"
        "Remember without it disputes wouldn’t be resolved. Once filled proceed with\n"
        "Specifications of the seller or buyer with /seller or /buyer [CRYPTO ADDRESS]"
    )


# ============================================================
# BUYER / SELLER
# ============================================================

@dp.message(Command("buyer"))
async def buyer(
    message: Message,
    command: CommandObject,
):
    e = get_trade(message.from_user.id)

    if not e:
        e = new_trade(
            message.from_user.id,
            display_name(message.from_user),
        )

    address = (command.args or "").strip()

    if not address:
        await message.answer(
            "Please use /buyer [DEPOSIT ADDRESS]"
        )
        return

    e["buyer_id"] = message.from_user.id
    e["buyer_username"] = message.from_user.username
    e["buyer_wallet"] = address

    await message.answer(
        f"📌 <b>ESCROW-ROLE DECLARATION</b>\n\n"
        f"⚡ <b>BUYER @{message.from_user.username or message.from_user.first_name} | Userid: [{message.from_user.id}]</b>\n\n"
        f"✅ <b>BUYER WALLET</b>\n"
        f"<code>{address}</code>\n\n"
        "Note: If you don't see any address, then your address will used from saved addresses after selecting token and chain for the current escrow."
    )

    await message.answer(
        "Please set seller using /seller [DEPOSIT ADDRESS]"
    )


@dp.message(Command("seller"))
async def seller(
    message: Message,
    command: CommandObject,
):
    e = get_trade(message.from_user.id)

    if not e:
        e = new_trade(
            message.from_user.id,
            display_name(message.from_user),
        )

    address = (command.args or "").strip()

    if not address:
        await message.answer(
            "Please use /seller [DEPOSIT ADDRESS]"
        )
        return

    e["seller_id"] = message.from_user.id
    e["seller_username"] = message.from_user.username
    e["seller_wallet"] = address

    await message.answer(
        f"📌 <b>ESCROW-ROLE DECLARATION</b>\n\n"
        f"⚡ <b>SELLER @{message.from_user.username or message.from_user.first_name} | Userid: [{message.from_user.id}]</b>\n\n"
        f"✅ <b>SELLER WALLET</b>\n"
        f"<code>{address}</code>\n\n"
        "Note: If you don't see any address, then your address will used from saved addresses after selecting token and chain for the current escrow."
    )

    await message.answer(
        "Use /token to Choose crypto."
    )


# ============================================================
# TOKEN
# ============================================================

@dp.message(Command("token"))
async def token(message: Message):
    await message.answer(
        "<b>choose token from the list below</b>",
        reply_markup=token_keyboard(),
    )


async def select_token(callback: CallbackQuery, crypto: str):
    e = get_trade(callback.from_user.id)

    if not e:
        e = new_trade(
            callback.from_user.id,
            display_name(callback.from_user),
        )

    e["crypto"] = crypto

    if crypto == "USDT":
        await callback.message.edit_text(
            "📌 <b>ESCROW-CRYPTO DECLARATION</b>\n\n"
            "✅ <b>CRYPTO</b>\n"
            "USDT\n\n"
            "<b>choose network from the list below for USDT</b>",
            reply_markup=network_keyboard(),
        )
    else:
        e["network"] = None
        await callback.message.answer(
            declaration(e),
            reply_markup=accept_keyboard(),
        )

    await callback.answer()


@dp.callback_query(F.data == "token_ltc")
async def token_ltc(callback: CallbackQuery):
    await select_token(callback, "LTC")


@dp.callback_query(F.data == "token_btc")
async def token_btc(callback: CallbackQuery):
    await select_token(callback, "BTC")


@dp.callback_query(F.data == "token_usdt")
async def token_usdt(callback: CallbackQuery):
    await select_token(callback, "USDT")


@dp.callback_query(F.data == "net_bsc")
async def net_bsc(callback: CallbackQuery):
    e = get_trade(callback.from_user.id)

    if not e:
        e = new_trade(
            callback.from_user.id,
            display_name(callback.from_user),
        )

    e["network"] = "BSC"

    await callback.message.answer(
        declaration(e),
        reply_markup=accept_keyboard(),
    )

    await callback.answer()


@dp.callback_query(F.data == "net_tron")
async def net_tron(callback: CallbackQuery):
    e = get_trade(callback.from_user.id)

    if not e:
        e = new_trade(
            callback.from_user.id,
            display_name(callback.from_user),
        )

    e["network"] = "TRON"

    await callback.message.answer(
        declaration(e),
        reply_markup=accept_keyboard(),
    )

    await callback.answer()


@dp.callback_query(F.data == "back_token")
async def back_token(callback: CallbackQuery):
    await callback.message.edit_text(
        "<b>choose token from the list below</b>",
        reply_markup=token_keyboard(),
    )
    await callback.answer()


# ============================================================
# ACCEPT / REJECT
# ============================================================

@dp.callback_query(F.data == "accept_trade")
async def accept_trade(callback: CallbackQuery):
    e = get_trade(callback.from_user.id)

    if not e:
        await callback.answer(
            "No active escrow found.",
            show_alert=True,
        )
        return

    await callback.message.answer(
        transaction_information(e)
    )

    await callback.answer("Accepted ✅")


@dp.callback_query(F.data == "reject_trade")
async def reject_trade(callback: CallbackQuery):
    e = get_trade(callback.from_user.id)

    if e:
        e["crypto"] = None
        e["network"] = None

    await callback.message.answer(
        "❌ Escrow declaration rejected."
    )

    await callback.answer("Rejected ❌")


# ============================================================
# DEPOSIT / PAYMENT BUTTON
# ============================================================

@dp.message(Command("deposit"))
async def deposit(message: Message):
    e = get_trade(message.from_user.id)

    if not e:
        await message.answer(
            "❌ No active escrow found."
        )
        return

    await message.answer(
        transaction_information(e),
        reply_markup=deposit_keyboard(),
    )


@dp.callback_query(F.data == "check_payment")
async def check_payment(callback: CallbackQuery):
    # Kept as a safe status button until a real payment/blockchain
    # verification service is connected.
    await callback.answer(
        "Payment status is not available yet.",
        show_alert=True,
    )


# ============================================================
# DISPUTE
# ============================================================

@dp.message(Command("dispute"))
async def dispute(message: Message):
    await message.answer(
        "📌 Dispute request received.\n\n"
        "An arbitrator can review the escrow."
    )


# ============================================================
# START BOT
# ============================================================

async def main():
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML
        ),
    )

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
