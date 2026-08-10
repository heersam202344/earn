"""
PAGAL Escrow Bot - Database Layer
"""
import sqlite3
import logging
from datetime import datetime
from config import DB_NAME

logger = logging.getLogger(__name__)

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

        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                bio TEXT DEFAULT '',
                has_bot_in_bio INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS escrows (
                escrow_id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER UNIQUE,
                group_name TEXT,
                creator_id INTEGER,
                creator_username TEXT,
                creator_name TEXT,
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
                message_ids TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS saved_wallets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                token TEXT,
                network TEXT,
                address TEXT,
                UNIQUE(user_id, token, network)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS deposits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                escrow_id INTEGER,
                tx_hash TEXT,
                amount REAL,
                confirmed INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()
        logger.info("Database initialized")

    def add_user(self, user_id, username, first_name, bio=""):
        conn = self.get_conn()
        cur = conn.cursor()
        from config import BOT_USERNAME
        has_bot = 1 if f"@{BOT_USERNAME}" in (bio or "") else 0
        cur.execute("""
            INSERT OR REPLACE INTO users (user_id, username, first_name, bio, has_bot_in_bio)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, username, first_name, bio, has_bot))
        conn.commit()
        conn.close()

    def get_user(self, user_id):
        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

    def create_escrow(self, group_id, creator_id, creator_username, creator_name, group_name):
        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO escrows (group_id, creator_id, creator_username, creator_name, group_name, status)
            VALUES (?, ?, ?, ?, ?, 'pending')
        """, (group_id, creator_id, creator_username, creator_name, group_name))
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
        self.update_escrow(escrow_id, escrow_address=address, status='awaiting_deposit')

    def confirm_deposit(self, escrow_id, amount):
        self.update_escrow(escrow_id, amount_received=amount, status='deposited')

    def complete_escrow(self, escrow_id):
        self.update_escrow(escrow_id, status='completed')

    def refund_escrow(self, escrow_id):
        self.update_escrow(escrow_id, status='refunded')

    def add_message_id(self, escrow_id, msg_id):
        esc = self.get_escrow_by_id(escrow_id)
        ids = esc.get('message_ids', '')
        ids = f"{ids},{msg_id}" if ids else str(msg_id)
        self.update_escrow(escrow_id, message_ids=ids)

    def save_wallet(self, user_id, token, network, address):
        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT OR REPLACE INTO saved_wallets (user_id, token, network, address)
            VALUES (?, ?, ?, ?)
        """, (user_id, token, network, address))
        conn.commit()
        conn.close()

    def get_saved_wallet(self, user_id, token, network):
        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM saved_wallets WHERE user_id = ? AND token = ? AND network = ?",
                    (user_id, token, network))
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_all_escrows(self):
        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM escrows ORDER BY created_at DESC")
        rows = cur.fetchall()
        conn.close()
        return [dict(row) for row in rows]
