"""
PAGAL Escrow Bot - Utilities & Auto-Correction
"""
import difflib
import logging
from config import BOT_USERNAME

logger = logging.getLogger(__name__)

# All known bot commands
KNOWN_COMMANDS = [
    'start', 'menu', 'escrow', 'dd', 'buyer', 'seller',
    'token', 'deposit', 'release', 'refund', 'dispute',
    'help', 'commands', 'accept', 'reject'
]

def auto_correct_command(text):
    """
    Auto-corrects misspelled commands.
    Examples: /byer -> /buyer, /seler -> /seller, /depo -> /deposit
    Returns: (corrected_full_command, base_command) or (None, None)
    """
    if not text or not text.startswith('/'):
        return None, None

    # Remove @botname if present: /buyer@PagaLEscrowBot -> /buyer
    parts = text[1:].split()
    raw_cmd_part = parts[0]

    if '@' in raw_cmd_part:
        raw_cmd, mentioned_bot = raw_cmd_part.split('@', 1)
    else:
        raw_cmd = raw_cmd_part
        mentioned_bot = None

    raw_cmd = raw_cmd.lower()
    args = parts[1:] if len(parts) > 1 else []

    # Exact match - no correction needed
    if raw_cmd in KNOWN_COMMANDS:
        return None, None

    # Try fuzzy matching
    matches = difflib.get_close_matches(raw_cmd, KNOWN_COMMANDS, n=1, cutoff=0.5)
    if matches:
        corrected_cmd = matches[0]
        corrected = f"/{corrected_cmd}"
        if args:
            corrected += " " + " ".join(args)
        if mentioned_bot:
            corrected += f"@{mentioned_bot}"
        return corrected, corrected_cmd

    return None, None

def format_wallet(wallet, max_len=50):
    """Format wallet address for display"""
    if len(wallet) > max_len:
        return wallet[:max_len] + "..."
    return wallet

def escape_html(text):
    """Escape HTML special characters"""
    if not text:
        return ""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def get_fee_for_users(buyer_bio, seller_bio):
    """Calculate fee based on whether users have bot in bio"""
    from config import ESCROW_FEE_DEFAULT, ESCROW_FEE_PROMO, BOT_USERNAME
    bot_mention = f"@{BOT_USERNAME}"

    buyer_has = bot_mention in (buyer_bio or "")
    seller_has = bot_mention in (seller_bio or "")

    if buyer_has and seller_has:
        return ESCROW_FEE_PROMO
    return ESCROW_FEE_DEFAULT
