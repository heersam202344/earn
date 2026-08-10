"""
PAGAL Escrow Bot - Inline Keyboards (exactly as per screenshots)
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def welcome_keyboard():
    """Main welcome menu keyboard - Screenshot #1"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("COMMANDS LIST 🤖", callback_data='commands_list')],
        [InlineKeyboardButton("☎️ CONTACT", callback_data='contact')],
        [InlineKeyboardButton("Updates ⤴️", url="https://t.me/pagal_updates"),
         InlineKeyboardButton("Vouchers ✅", url="https://t.me/pagal_vouches")],
        [InlineKeyboardButton("WHAT IS ESCROW ❓", callback_data='what_is_escrow'),
         InlineKeyboardButton("Instructions 👨‍💻", callback_data='instructions')],
        [InlineKeyboardButton("Terms 📝", callback_data='terms')],
        [InlineKeyboardButton("Invites 👤", callback_data='invites')]
    ])

def escrow_type_keyboard():
    """P2P vs Product Deal - Screenshot #1 bottom"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("P2P", callback_data='escrow_p2p'),
         InlineKeyboardButton("Product Deal", callback_data='escrow_product')]
    ])

def token_keyboard():
    """Token selection - Screenshot #9"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("LTC", callback_data='token_LTC'),
         InlineKeyboardButton("BTC", callback_data='token_BTC')],
        [InlineKeyboardButton("USDT", callback_data='token_USDT')]
    ])

def network_keyboard(token):
    """Network selection - Screenshot #10"""
    if token == "USDT":
        buttons = [
            [InlineKeyboardButton("BSC[BEP20]", callback_data='net_BSC'),
             InlineKeyboardButton("TRON[TRC20]", callback_data='net_TRON')]
        ]
    elif token == "BTC":
        buttons = [[InlineKeyboardButton("BTC Network", callback_data='net_BTC')]]
    elif token == "LTC":
        buttons = [[InlineKeyboardButton("LTC Network", callback_data='net_LTC')]]
    else:
        buttons = [[InlineKeyboardButton("BSC[BEP20]", callback_data='net_BSC')]]

    buttons.append([InlineKeyboardButton("Back ⬅️", callback_data='back_token')])
    return InlineKeyboardMarkup(buttons)

def accept_reject_keyboard():
    """Accept/Reject - Screenshot #11"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Accept ✅", callback_data='accept_escrow'),
         InlineKeyboardButton("Reject ❌", callback_data='reject_escrow')]
    ])

def check_payment_keyboard():
    """Check Payment button - Screenshot #15"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Check Payment", callback_data='check_payment')]
    ])

def how_to_use_keyboard():
    """How To Use Bot button - Screenshot #5"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("How To Use Bot ❓", callback_data='how_to_use')]
    ])

def commands_list_text():
    return """📋 <b>COMMANDS LIST</b> 🤖

/start - Start the bot
/menu - Show main menu  
/escrow - Create new escrow (in group)
/dd - Fill Deal Details
/buyer [ADDRESS] - Set buyer wallet
/seller [ADDRESS] - Set seller wallet
/token - Choose cryptocurrency
/deposit - Generate deposit address
/release - Release funds to buyer
/refund - Refund funds to seller
/dispute - Raise a dispute"""
