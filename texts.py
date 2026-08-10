"""
PAGAL Escrow Bot - Message Texts (exactly as per screenshots)
All texts use HTML parse mode for bold, code, etc.
"""

from config import BOT_USERNAME, ESCROW_FEE_DEFAULT

WELCOME_TEXT = """💫 @PagaLEscrowBot 💫
Your Trustworthy Telegram Escrow Service

Welcome to @PagaLEscrowBot. This bot provides a reliable escrow service for your transactions on Telegram.
Avoid scams, your funds are safeguarded throughout your deals. If you run into any issues, simply type /dispute and an arbitrator will join the group chat within 24 hours.

🏧 <b>ESCROW FEE:</b>
1.0% for P2P and 1.0% for OTC Flat

🌐 (UPDATES) - (VOUCHES) ✅

💬 Proceed with /escrow (to start with a new escrow)

⚠️ <b>IMPORTANT</b> - Make sure coin is same of Buyer and Seller else you may loose your coin.

💡 Type /menu to summon a menu with all bots features"""

ESCROW_TYPE_TEXT = "Please select your escrow type from below."

CREATING_ESCROW_TEXT = "Creating a safe trading place for you, please wait..."

GROUP_CREATED_TEXT = """📍 <b>Escrow Group Created</b>

Creator: {creator_name}

Join this escrow group and share the link with the buyer and seller.

{invite_link}

⚠️ <b>Note:</b> This link is for 2 members only—third parties are not allowed to join."""

GROUP_WELCOME_PIN = "📍 Hey there traders! Welcome to our escrow service."

GROUP_START_TEXT = """📍 Hey there traders! Welcome to our escrow service.
✅ Please start with /dd command and fill the DealInfo Form"""

DD_TEXT = """Hello there,
Kindly tell deal details i.e.

Quantity -
Rate -
Conditions (if any) -

Remember without it disputes wouldn't be resolved. Once filled proceed with Specifications of the seller or buyer with /seller or /buyer [CRYPTO ADDRESS]"""

def buyer_declared_text(username, user_id, wallet):
    return f"""📍 <b>ESCROW-ROLE DECLARATION</b>

⚡ <b>BUYER</b> @{username} | Userid: <code>[{user_id}]</code>

✅ <b>BUYER WALLET</b>
<code>{wallet}</code>

Note: If you don't see any address, then your address will used from saved addresses after selecting token and chain for the current escrow."""

def seller_declared_text(username, user_id, wallet):
    return f"""📍 <b>ESCROW-ROLE DECLARATION</b>

⚡ <b>SELLER</b> @{username} | Userid: <code>[{user_id}]</code>

✅ <b>SELLER WALLET</b>
<code>{wallet}</code>

Note: If you don't see any address, then your address will used from saved addresses after selecting token and chain for the current escrow."""

TOKEN_PROMPT = "Use /token to Choose crypto."

def crypto_declaration_text(token):
    return f"""📍 <b>ESCROW-CRYPTO DECLARATION</b>

✅ <b>CRYPTO</b>
{token}

choose network from the list below for {token}"""

def escrow_declaration_text(seller_username, seller_id, token, network):
    return f"""📍 <b>ESCROW DECLARATION</b>

⚡ Seller @{seller_username} | Userid: <code>[{seller_id}]</code>

✅ {token} CRYPTO
✅ {network} NETWORK"""

def full_declaration_text(buyer_username, buyer_id, seller_username, seller_id, token, network):
    return f"""📍 <b>ESCROW DECLARATION</b>

⚡ Buyer @{buyer_username} | Userid: <code>[{buyer_id}]</code>
⚡ Seller @{seller_username} | Userid: <code>[{seller_id}]</code>

✅ {token} CRYPTO
✅ {network} NETWORK"""

def transaction_info_text(escrow_id, seller_username, seller_id, seller_wallet, 
                          buyer_username, buyer_id, buyer_wallet, token, network, trade_time):
    return f"""📍 <b>TRANSACTION INFORMATION</b> <code>[{escrow_id}]</code>

⚡ <b>SELLER</b>
@{seller_username} | <code>[{seller_id}]</code>
<code>{seller_wallet}</code>[{token}][{network}]

⚡ <b>BUYER</b>
@{buyer_username} | <code>[{buyer_id}]</code>
<code>{buyer_wallet}</code>[{token}][{network}]

⏰ Trade Start Time: {trade_time}

⚠️ <b>IMPORTANT:</b> Make sure to finalise and agree each-others terms before depositing.

📝 Please use /deposit command to generate a deposit address for your trade."""

def fee_notice_text(fee_percent):
    return f"Your Fee is {fee_percent}% as both buyer and seller are not using @PagaLEscrowBot in your bio."

def deposit_request_text():
    return "Requesting a deposit address for you, please wait..."

def deposit_info_text(escrow_id, seller_username, seller_id, seller_wallet,
                      buyer_username, buyer_id, buyer_wallet, escrow_address,
                      token, network, trade_time, expiry_minutes):
    return f"""📍 <b>TRANSACTION INFORMATION</b> <code>[{escrow_id}]</code>

⚡ <b>SELLER</b>
@{seller_username} | <code>[{seller_id}]</code>
<code>{seller_wallet}</code>[{token}][{network}]

⚡ <b>BUYER</b>
@{buyer_username} | <code>[{buyer_id}]</code>
<code>{buyer_wallet}</code>[{token}][{network}]

🟢 <b>ESCROW ADDRESS</b>
<code>{escrow_address}</code> [{token}][{network}]

Seller [@{seller_username}] Will Pay on the Escrow Address, And Click On Check Payment.

Amount Received: 0.00000 [0.00$]

⏰ Trade Start Time: {trade_time}
⏰ Address Reset In: {expiry_minutes}.00 Min

📝 Note: Address will reset after the given time, so make sure to deposit in the bot before the address expires.
Useful commands:
📝 /release = Will Release The Funds To Buyer.
📝 /refund = Will Refund The Funds To Seller.

Remember, once commands are used payment will be released, there is no revert!"""

AUTO_CORRECT_TEXT = "🤔 Did you mean <code>{corrected}</code>?

Running <b>/{cmd}</b> for you..."

CONTACT_TEXT = "☎️ <b>CONTACT</b>

For support, contact: @PagaLSupport"
WHAT_IS_ESCROW_TEXT = "❓ <b>WHAT IS ESCROW?</b>

Escrow is a financial arrangement where a third party holds and regulates payment of the funds required for two parties involved in a given transaction."
INSTRUCTIONS_TEXT = "👨‍💻 <b>INSTRUCTIONS</b>

1. Start with /escrow
2. Set buyer and seller wallets
3. Choose crypto and network
4. Accept the deal
5. Use /deposit to get address
6. Use /release or /refund"
TERMS_TEXT = "📝 <b>TERMS</b>

By using this bot, you agree to our terms of service. Fee is 1.0% per transaction."
INVITES_TEXT = "👤 <b>INVITES</b>

Invite your friends and earn rewards!"
