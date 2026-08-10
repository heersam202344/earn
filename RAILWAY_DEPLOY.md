# 🚀 Railway Deployment Guide - PAGAL Escrow Bot

## Step 1: Upload to GitHub

```bash
cd pagal_escrow_bot
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/pagal-escrow-bot.git
git push -u origin main
```

## Step 2: Create Railway Project

1. Go to https://railway.app
2. Login with GitHub
3. Click **New Project**
4. Select **Deploy from GitHub repo**
5. Choose `pagal-escrow-bot`

## Step 3: Add Environment Variables

Go to your project → **Variables** tab → Add these:

| Variable | Value |
|----------|-------|
| BOT_TOKEN | 8821716993:AAGKTRUvAIh3WWQTIrtsfIh03lxpxgb847k |
| API_ID | 38355068 |
| API_HASH | cd198c10920bf62dde9581df6888a2a4 |
| STRING_SESSION | 1BVtsOLkBu7a8hRRAmcyruzFj0ekIOGjZx2nGdG0FxepH2P0-T9Cb-gSsd9qOK-9GWiqE_KclQy8ataZimb05RereWh9oEhFeULrubg2XEHpNsSBG1WI_7igCletXSIShGhsxTWte-bqSllNJ40-TPXFGOp5UvDegXJmC6uD7g-JIZVnprpvTKpu2z4Dxe9Hf2oGmC_kXuoJXYYVCxQxxq3gfAwqWlHafQGY1xcjYbS4DYYO-_W-ZQDRdvuIDRrLyCRpYvDonJutvk6lSyML8XXWHVy5wQ9p2AlTM9lu3dLf35dxrJDJbAmajqrG6PhHXWNhBSU0Pl7G8P9uTnA83W4Eh9DHeSB8= |
| ADMIN_IDS | 8309358370 |
| BTC_WALLET | bc1qkn9ufppulzlhkxa46hrspnd4l24s9px9pxuxet |
| LTC_WALLET | ltc1q8ywwttdd87s2h8ytr7d5ncc7029kjadrwvxph7 |
| USDT_BSC_WALLET | 0x16091F2b5F3FA0EA1B384DfA16b37316bac4FCB2 |
| USDT_TRC_WALLET | 0x16091F2b5F3FA0EA1B384DfA16b37316bac4FCB2 |
| BOT_USERNAME | PagaLEscrowBot |

## Step 4: Upload Template & Font

1. In Railway, go to your project → **Deployments**
2. Click on the latest deployment
3. Go to **Shell** tab
4. Upload `template.png` and `font.ttf` to the project root

OR add them to your GitHub repo before pushing.

## Step 5: Deploy

Click **Deploy** and wait for build to complete.

## Step 6: Check Logs

Go to **Logs** tab to see if bot started successfully.

You should see:
```
🤖 PAGAL Escrow Bot starting...
✅ Telethon connected successfully
```

## ⚠️ IMPORTANT NOTES

1. **Telegram Account**: The STRING_SESSION account must:
   - Have a profile photo
   - Have a username set
   - NOT have 2FA enabled (or provide password)
   - Be able to create groups

2. **Bot Permissions**: When adding bot to group, give these admin rights:
   - Delete Messages
   - Restrict Members  
   - Pin Messages
   - Change Group Info
   - Invite Users via Link

3. **Template Photo**: The `template.png` should be:
   - Square format (recommended 500x500 or 1000x1000)
   - Have space at bottom for text overlay
   - The bot will add: "💰 BUYER: @xxx" and "💰 SELLER: @xxx"

## 🎨 Font Setup

The screenshots show a bold, clean font. Recommended fonts:
- **Montserrat Bold**
- **Roboto Bold** 
- **Poppins Bold**

Download any bold TTF font and rename to `font.ttf`

## 🆘 Troubleshooting

**Bot not starting?**
- Check Railway logs for errors
- Verify BOT_TOKEN is correct
- Make sure API_ID is a number (not string)

**Telethon not connecting?**
- STRING_SESSION might be expired - regenerate using `generate_session.py`
- Make sure the phone number used for STRING_SESSION is valid
- The account might need to be logged in recently

**Group not auto-creating?**
- Telethon account might have group creation limits
- Try manually creating group and adding bot
- Check if account has spam restrictions

## 📞 Support

Admin ID: 8309358370
