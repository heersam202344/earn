"""
PAGAL Escrow Bot - Configuration
"""
import os

# Telegram Bot (from @BotFather)
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8821716993:AAGKTRUvAIh3WWQTIrtsfIh03lxpxgb847k")

# Admin IDs (comma separated) - for dispute alerts
ADMIN_IDS = [int(x.strip()) for x in os.environ.get("ADMIN_IDS", "8309358370").split(",") if x.strip()]

# Telethon User Account (for auto group creation)
API_ID = int(os.environ.get("API_ID", "38355068"))
API_HASH = os.environ.get("API_HASH", "cd198c10920bf62dde9581df6888a2a4")
STRING_SESSION = os.environ.get("STRING_SESSION", "1BVtsOLkBu7a8hRRAmcyruzFj0ekIOGjZx2nGdG0FxepH2P0-T9Cb-gSsd9qOK-9GWiqE_KclQy8ataZimb05RereWh9oEhFeULrubg2XEHpNsSBG1WI_7igCletXSIShGhsxTWte-bqSllNJ40-TPXFGOp5UvDegXJmC6uD7g-JIZVnprpvTKpu2z4Dxe9Hf2oGmC_kXuoJXYYVCxQxxq3gfAwqWlHafQGY1xcjYbS4DYYO-_W-ZQDRdvuIDRrLyCRpYvDonJutvk6lSyML8XXWHVy5wQ9p2AlTM9lu3dLf35dxrJDJbAmajqrG6PhHXWNhBSU0Pl7G8P9uTnA83W4Eh9DHeSB8=")

# Escrow Settings
ESCROW_FEE_DEFAULT = 1.0
ESCROW_FEE_PROMO = 0.0
ADDRESS_EXPIRY_MINUTES = 20

# Wallet addresses for each crypto
WALLETS = {
    "BTC": os.environ.get("BTC_WALLET", "bc1qkn9ufppulzlhkxa46hrspnd4l24s9px9pxuxet"),
    "USDT_BSC": os.environ.get("USDT_BSC_WALLET", "0x16091F2b5F3FA0EA1B384DfA16b37316bac4FCB2"),
    "USDT_TRC": os.environ.get("USDT_TRC_WALLET", "0x16091F2b5F3FA0EA1B384DfA16b37316bac4FCB2"),
    "LTC": os.environ.get("LTC_WALLET", "ltc1q8ywwttdd87s2h8ytr7d5ncc7029kjadrwvxph7"),
}

# Database
DB_NAME = os.environ.get("DB_NAME", "pagal_escrow.db")

# Photo Template
TEMPLATE_PATH = os.environ.get("TEMPLATE_PATH", "template.png")
FONT_PATH = os.environ.get("FONT_PATH", "font.ttf")

# Bot Info
BOT_USERNAME = os.environ.get("BOT_USERNAME", "PagaLEscrowBot")
BOT_LINK = f"https://t.me/{BOT_USERNAME}"
