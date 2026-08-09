import asyncio
import os
from typing import Optional

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup


BOT_TOKEN = os.environ["BOT_TOKEN"]
BOT_USERNAME = os.getenv("BOT_USERNAME", "PagaLEscrowBot").lstrip("@")
PAGAL_WORLD_URL = os.getenv("PAGAL_WORLD_URL", "https://t.me/PagalWorlddhehe")

# Optional local images. Telegram file_id values can also be used in a real deployment.
GROUP_INITIAL_PHOTO = os.getenv("GROUP_INITIAL_PHOTO", "")
GROUP_TRANSACTION_PHOTO = os.getenv("GROUP_TRANSACTION_PHOTO", "")

escrows = {}
next_trade_id = 10000000


def display_name(user):
    full = f"{getattr(user, 'first_name', '') or ''} {getattr(user, 'last_name', '') or ''}".strip()
    return full or getattr(user, "username", None) or "User"


def new_trade(user_id, creator_name):
    global next_trade_id
    trade_id = str(next_trade_id)
    next_trade_id += 1
    e = {
        "trade_code": trade_id,
        "creator_id": user_id,
        "creator_name": creator_name,
        "deal_type": None,
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
        "start_time": "--/--/-- --:--:--",
        "deposit_address": None,
        "status": "created",
    }
    escrows[user_id] = e
    return e


def get_trade(user_id):
    return escrows.get(user_id)


def world_button(text):
    return InlineKeyboardButton(text=text, url=PAGAL_WORLD_URL)


def start_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="P2P", callback_data="type_p2p"),
            InlineKeyboardButton(text="Product Deal", callback_data="type_product"),
        ],
        [world_button("COMMANDS LIST 🤖")],
        [world_button("☎️ CONTACT")],
        [world_button("Updates 🔄"), world_button("Vouches ✔️")],
        [world_button("WHAT IS ESCROW ?"), world_button("Instructions 👩‍🏫")],
        [world_button("Terms 📝")],
        [world_button("Invites 👤")],
    ])


def escrow_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="P2P", callback_data="type_p2p"),
            InlineKeyboardButton(text="Product Deal", callback_data="type_product"),
        ]
    ])


def token_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="LTC", callback_data="token_ltc"),
            InlineKeyboardButton(text="BTC", callback_data="token_btc"),
        ],
        [InlineKeyboardButton(text="USDT", callback_data="token_usdt")],
    ])


def network_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="BSC[BEP20]", callback_data="net_bsc"),
            InlineKeyboardButton(text="TRON[TRC20]", callback_data="net_tron"),
        ],
        [InlineKeyboardButton(text="Back ⬅️", callback_data="back_token")],
    ])


def accept_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Accept ✅", callback_data="accept_trade"),
            InlineKeyboardButton(text="Reject ❌", callback_data="reject_trade"),
        ]
    ])


def deposit_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Check Payment", callback_data="check_payment")]
    ])


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

⏰ <b>Trade Start Time:</b> {e["start_time"]}

⚠️ <b>IMPORTANT:</b> Make sure to finalise and agree each-other's terms before depositing.

📄 Please use /deposit command to generate a deposit address for your trade."""


dp = Dispatcher()


@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        WELCOME.format(url=PAGAL_WORLD_URL),
        reply_markup=start_keyboard(),
        disable_web_page_preview=True,
    )
    await message.answer(
        "Please select your escrow type from below.",
        reply_markup=escrow_keyboard(),
    )


@dp.message(Command("menu"))
async def menu(message: Message):
    await message.answer("💡 <b>Commands / Menu</b>", reply_markup=start_keyboard())


@dp.message(Command("escrow"))
async def escrow(message: Message):
    await message.answer(
        "Please select your escrow type from below.",
        reply_markup=escrow_keyboard(),
    )


async def begin_type(callback: CallbackQuery):
    e = get_trade(callback.from_user.id)
    if not e:
        e = new_trade(callback.from_user.id, display_name(callback.from_user))

    e["deal_type"] = "P2P" if callback.data == "type_p2p" else "Product Deal"

    await callback.message.edit_text(
        "Creating a safe trading place for you, please wait..."
    )

    # Safe placeholder: Bot API cannot create a Telegram group as a user account.
    # The generated link below is intentionally not presented as a real payment escrow.
    await callback.message.edit_text(
        f"<b>Escrow Group Created</b>\n\n"
        f"Creator: {e['creator_name']}\n"
        f"Deal Type: {e['deal_type']}\n"
        f"Trade ID: <code>{e['trade_code']}</code>\n\n"
        f"⚠️ Group creation/invitation must be connected to your own Telegram "
        f"account integration before a real group link can be generated.\n\n"
        f"Continue in the group with /dd once your group is ready.",
        disable_web_page_preview=True,
    )
    await callback.answer()


@dp.callback_query(F.data.in_(["type_p2p", "type_product"]))
async def type_selected(callback: CallbackQuery):
    await begin_type(callback)


@dp.message(Command("dd"))
async def dd(message: Message):
    e = get_trade(message.from_user.id)
    if not e:
        e = new_trade(message.from_user.id, display_name(message.from_user))

    await message.answer(
        "Hello there,\n"
        "Kindly tell deal details i.e.\n\n"
        "Quantity -\n"
        "Rate -\n"
        "Conditions (if any) -\n\n"
        "Remember without it disputes wouldn’t be resolved. Once filled proceed with\n"
        "Specifications of the seller or buyer with /seller or /buyer [CRYPTO ADDRESS]"
    )


@dp.message(Command("buyer"))
async def buyer(message: Message, command: CommandObject):
    e = get_trade(message.from_user.id)
    if not e:
        e = new_trade(message.from_user.id, display_name(message.from_user))

    address = (command.args or "").strip()
    if not address:
        await message.answer("Please use /buyer [DEPOSIT ADDRESS]")
        return

    e["buyer_id"] = message.from_user.id
    e["buyer_username"] = message.from_user.username or message.from_user.first_name
    e["buyer_wallet"] = address

    await message.answer(
        f"📌 <b>ESCROW-ROLE DECLARATION</b>\n\n"
        f"⚡ <b>BUYER @{e['buyer_username']} | Userid: [{e['buyer_id']}]</b>\n\n"
        f"✅ <b>BUYER WALLET</b>\n<code>{address}</code>\n\n"
        "Note: If you don't see any address, then your address will used from saved addresses after selecting token and chain for the current escrow."
    )
    await message.answer("Please set seller using /seller [DEPOSIT ADDRESS]")


@dp.message(Command("seller"))
async def seller(message: Message, command: CommandObject):
    e = get_trade(message.from_user.id)
    if not e:
        e = new_trade(message.from_user.id, display_name(message.from_user))

    address = (command.args or "").strip()
    if not address:
        await message.answer("Please use /seller [DEPOSIT ADDRESS]")
        return

    e["seller_id"] = message.from_user.id
    e["seller_username"] = message.from_user.username or message.from_user.first_name
    e["seller_wallet"] = address

    await message.answer(
        f"📌 <b>ESCROW-ROLE DECLARATION</b>\n\n"
        f"⚡ <b>SELLER @{e['seller_username']} | Userid: [{e['seller_id']}]</b>\n\n"
        f"✅ <b>SELLER WALLET</b>\n<code>{address}</code>\n\n"
        "Note: If you don't see any address, then your address will used from saved addresses after selecting token and chain for the current escrow."
    )
    await message.answer("Use /token to Choose crypto.")


@dp.message(Command("token"))
async def token(message: Message):
    await message.answer(
        "<b>choose token from the list below</b>",
        reply_markup=token_keyboard(),
    )


async def select_token(callback: CallbackQuery, crypto: str):
    e = get_trade(callback.from_user.id)
    if not e:
        e = new_trade(callback.from_user.id, display_name(callback.from_user))

    e["crypto"] = crypto

    if crypto == "USDT":
        await callback.message.edit_text(
            "📌 <b>ESCROW-CRYPTO DECLARATION</b>\n\n"
            "✅ <b>CRYPTO</b>\nUSDT\n\n"
            "<b>choose network from the list below for USDT</b>",
            reply_markup=network_keyboard(),
        )
    else:
        e["network"] = crypto
        await callback.message.answer(declaration(e), reply_markup=accept_keyboard())

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


async def select_network(callback: CallbackQuery, network: str):
    e = get_trade(callback.from_user.id)
    if not e:
        e = new_trade(callback.from_user.id, display_name(callback.from_user))

    e["network"] = network
    await callback.message.answer(declaration(e), reply_markup=accept_keyboard())
    await callback.answer()


@dp.callback_query(F.data == "net_bsc")
async def net_bsc(callback: CallbackQuery):
    await select_network(callback, "BSC")


@dp.callback_query(F.data == "net_tron")
async def net_tron(callback: CallbackQuery):
    await select_network(callback, "TRON")


@dp.callback_query(F.data == "back_token")
async def back_token(callback: CallbackQuery):
    await callback.message.edit_text(
        "<b>choose token from the list below</b>",
        reply_markup=token_keyboard(),
    )
    await callback.answer()


@dp.callback_query(F.data == "accept_trade")
async def accept_trade(callback: CallbackQuery):
    e = get_trade(callback.from_user.id)
    if not e:
        await callback.answer("No active escrow found.", show_alert=True)
        return

    from datetime import datetime, timezone
    e["start_time"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    e["status"] = "accepted"

    await callback.message.answer(transaction_information(e))
    await callback.answer("Accepted ✅")


@dp.callback_query(F.data == "reject_trade")
async def reject_trade(callback: CallbackQuery):
    e = get_trade(callback.from_user.id)
    if e:
        e["status"] = "rejected"

    await callback.message.answer("❌ Escrow declaration rejected.")
    await callback.answer("Rejected")


@dp.message(Command("deposit"))
async def deposit(message: Message):
    e = get_trade(message.from_user.id)
    if not e:
        await message.answer("❌ No active escrow found. Start with /escrow.")
        return

    if e["status"] != "accepted":
        await message.answer("⚠️ Accept the escrow declaration before using /deposit.")
        return

    # Non-custodial/demo flow. No funds are generated, held, or released.
    e["status"] = "awaiting_payment"
    await message.answer(
        f"📌 <b>DEPOSIT INFORMATION [{e['trade_code']}]</b>\n\n"
        f"⚡ Crypto: <b>{e['crypto'] or '-'}</b>\n"
        f"⚡ Network: <b>{e['network'] or '-'}</b>\n\n"
        "⚠️ <b>DEMO / NON-CUSTODIAL FLOW</b>\n"
        "A real blockchain deposit address is not generated by this demo.\n"
        "Connect a legitimate payment provider or wallet service before accepting funds.\n\n"
        "Use the button below to check the configured payment integration.",
        reply_markup=deposit_keyboard(),
    )


@dp.callback_query(F.data == "check_payment")
async def check_payment(callback: CallbackQuery):
    e = get_trade(callback.from_user.id)
    if not e:
        await callback.answer("No active escrow found.", show_alert=True)
        return

    await callback.answer(
        "Payment verification is not connected in this demo.",
        show_alert=True,
    )


@dp.message(Command("release"))
async def release(message: Message):
    await message.answer(
        "⚠️ Release is disabled in this demo. Connect a legitimate, "
        "non-custodial payment/escrow provider before handling funds."
    )


@dp.message(Command("refund"))
async def refund(message: Message):
    await message.answer(
        "⚠️ Refund is disabled in this demo. Connect a legitimate, "
        "non-custodial payment/escrow provider before handling funds."
    )


@dp.message(Command("dispute"))
async def dispute(message: Message):
    await message.answer(
        "📌 Dispute request received.\n\n"
        "An administrator/arbitrator can review the trade manually."
    )


async def main():
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
