import bcrypt
import sqlite3
import jwt
from datetime import datetime, timedelta
from config import JWT_SECRET

def generate_token(user_email, subscribed):
    payload = {
        "email": user_email,
        "subscribed": subscribed,
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def verify_token(token):
    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return decoded
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def create_user_table():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            password TEXT,
            usage_count INTEGER,
            subscribed INTEGER
        )
    """)
    conn.commit()
    conn.close()

def add_user(email, password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    c.execute("INSERT INTO users (email, password, usage_count, subscribed) VALUES (?, ?, ?, ?)",
              (email, hashed_pw, 0, 0))
    conn.commit()
    conn.close()

def authenticate_user(email, password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE email=?", (email,))
    result = c.fetchone()
    conn.close()
    if result and bcrypt.checkpw(password.encode(), result[0].encode()):
        return True
    return False

def get_user(email):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT usage_count, subscribed FROM users WHERE email=?", (email,))
    result = c.fetchone()
    conn.close()
    return result

def update_usage(email):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("UPDATE users SET usage_count = usage_count + 1 WHERE email=?", (email,))
    conn.commit()
    conn.close()

def set_subscribed(email):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("UPDATE users SET subscribed = 1 WHERE email=?", (email,))
    conn.commit()
    conn.close()

def create_payments_table():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            gateway TEXT,
            amount INTEGER,
            status TEXT,
            plan TEXT,
            subscription_id TEXT,
            order_id TEXT,
            payment_id TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    
def add_payment_record(email, gateway, amount, status, plan=None, subscription_id=None, order_id=None, payment_id=None):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO payments (email, gateway, amount, status, plan, subscription_id, order_id, payment_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (email, gateway, amount, status, plan, subscription_id, order_id, payment_id))
    conn.commit()
    conn.close()
