# 🤖 PAGAL Escrow Bot

**Your Trustworthy Telegram Escrow Service**

Recreated exactly from the original @PagaLEscrowBot screenshots with auto group creation, photo generation, and full escrow flow.

---

## 📁 Project Structure

```
pagal_escrow_bot/
├── bot.py                 # Main bot application
├── config.py              # Configuration & environment variables
├── database.py            # SQLite database layer
├── keyboards.py           # Inline keyboard markups
├── texts.py               # All message templates
├── photo_gen.py           # Group photo generator
├── telethon_manager.py    # Auto group creation via MTProto
├── utils.py               # Auto-correction & helpers
├── requirements.txt       # Python dependencies
├── Procfile               # Railway deployment config
├── runtime.txt            # Python version
├── generate_session.py    # Telethon session generator
├── template.png           # ⬅️ YOUR group photo template (upload this)
├── font.ttf               # ⬅️ YOUR font file (upload this)
└── .gitignore
```

---

## 🔧 Prerequisites

### 1. Get API_ID and API_HASH
1. Go to [my.telegram.org](https://my.telegram.org)
2. Login with your phone number
3. Click **"API development tools"**
4. Create a new app (any name)
5. Copy **api_id** and **api_hash**

### 2. Get BOT_TOKEN
1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot`
3. Follow instructions and copy the token

### 3. Get STRING_SESSION
1. Install Telethon locally: `pip install telethon`
2. Run: `python generate_session.py`
3. Enter API_ID and API_HASH
4. Login with your phone number (OTP)
5. Copy the generated string

### 4. Get ADMIN_ID
1. Message [@userinfobot](https://t.me/userinfobot) on Telegram
2. Copy your numeric User ID

---

## 🚀 Railway Deployment

### Step 1: Upload to GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/pagal-escrow-bot.git
git push -u origin main
```

### Step 2: Deploy on Railway
1. Go to [railway.app](https://railway.app)
2. Click **New Project** → **Deploy from GitHub repo**
3. Select your repo
4. Go to **Variables** tab and add:

| Variable | Value | Example |
|----------|-------|---------|
| `BOT_TOKEN` | From BotFather | `123456:ABC-DEF...` |
| `API_ID` | From my.telegram.org | `12345678` |
| `API_HASH` | From my.telegram.org | `a1b2c3d4...` |
| `STRING_SESSION` | From generate_session.py | `1BQANOTEz...` |
| `ADMIN_IDS` | Your Telegram ID | `123456789` |
| `BTC_WALLET` | Your BTC address | `bc1qkn9ufppulzlhkxa46hrspnd4l24s9px9pxuxet` |
| `USDT_BSC_WALLET` | Your USDT BSC address | `0x...` |
| `USDT_TRC_WALLET` | Your USDT TRC20 address | `T...` |
| `LTC_WALLET` | Your LTC address | `L...` |
| `BOT_USERNAME` | Your bot username | `PagaLEscrowBot` |

5. Upload `template.png` and `font.ttf` to the project root
6. Click **Deploy**

---

## 🎨 Customization

### Group Photo Template
- Replace `template.png` with your P.A.G.A.L design
- The bot will overlay: `💰 BUYER: @username` and `💰 SELLER: @username`
- Adjust coordinates in `photo_gen.py` if text position needs changing

### Font
- Replace `font.ttf` with your preferred font
- The screenshots show a bold/clean sans-serif font

### Message Texts
- All texts are in `texts.py` - edit freely
- Uses HTML parse mode (`<b>`, `<code>`, etc.)

---

## 📸 Bot Flow (from Screenshots)

| Step | Command | Action |
|------|---------|--------|
| 1 | `/start` | Welcome + Menu |
| 2 | Click `P2P` | Auto-creates group |
| 3 | `/escrow` | Initializes escrow |
| 4 | `/dd` | Group name changes + Deal details |
| 5 | `/buyer [addr]` | Buyer declaration |
| 6 | `/seller [addr]` | Seller declaration |
| 7 | `/token` | Choose crypto |
| 8 | Select network | Network selection |
| 9 | Click `Accept` | Full declaration + Photo change |
| 10 | `/deposit` | Generate address + Pin message |
| 11 | `/release` | Release funds |
| 12 | `/refund` | Refund funds |

---

## ⚠️ Important Notes

- **Telethon** requires a real user account (not bot) to create groups
- The account used for STRING_SESSION will be the group creator
- Make sure that account has a profile picture and username set
- Bot must be added as admin with **Delete Messages**, **Restrict Members**, **Pin Messages**, **Change Group Info** permissions

---

## 🆘 Support

For issues, contact: @PagaLSupport

---

**Made with ❤️ for PAGAL Escrow**
