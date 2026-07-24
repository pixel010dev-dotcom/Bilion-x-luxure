"""Database module for Bilion Luxure - SQLite async wrapper."""
import sqlite3
import os
from datetime import datetime

DB_PATH = os.environ.get("DATABASE_URL", "data/bilion.db")


def get_db():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            coins INTEGER DEFAULT 0,
            diamonds INTEGER DEFAULT 0,
            plan TEXT DEFAULT 'free',
            plan_expires TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            payment_id TEXT,
            status TEXT DEFAULT 'pending',
            plan TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS generations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            type TEXT,
            prompt TEXT,
            cost INTEGER,
            result_url TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );
    """)
    conn.commit()
    conn.close()


def get_user(user_id: int):
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def create_user(user_id: int, username: str = None, first_name: str = None):
    conn = get_db()
    conn.execute(
        "INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
        (user_id, username, first_name),
    )
    conn.commit()
    conn.close()


def add_coins(user_id: int, amount: int):
    conn = get_db()
    conn.execute("UPDATE users SET coins = coins + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()


def add_diamonds(user_id: int, amount: int):
    conn = get_db()
    conn.execute("UPDATE users SET diamonds = diamonds + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()


def spend_coins(user_id: int, amount: int) -> bool:
    conn = get_db()
    user = conn.execute("SELECT coins FROM users WHERE user_id = ?", (user_id,)).fetchone()
    if user and user["coins"] >= amount:
        conn.execute("UPDATE users SET coins = coins - ? WHERE user_id = ?", (amount, user_id))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False


def spend_diamonds(user_id: int, amount: int) -> bool:
    conn = get_db()
    user = conn.execute("SELECT diamonds FROM users WHERE user_id = ?", (user_id,)).fetchone()
    if user and user["diamonds"] >= amount:
        conn.execute("UPDATE users SET diamonds = diamonds - ? WHERE user_id = ?", (amount, user_id))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False


def save_generation(user_id: int, gen_type: str, prompt: str, cost: int, result_url: str = None):
    conn = get_db()
    conn.execute(
        "INSERT INTO generations (user_id, type, prompt, cost, result_url) VALUES (?, ?, ?, ?, ?)",
        (user_id, gen_type, prompt, cost, result_url),
    )
    conn.commit()
    conn.close()


def create_payment(user_id: int, amount: float, payment_id: str, plan: str):
    conn = get_db()
    conn.execute(
        "INSERT INTO payments (user_id, amount, payment_id, plan) VALUES (?, ?, ?, ?)",
        (user_id, amount, payment_id, plan),
    )
    conn.commit()
    conn.close()


def update_payment_status(payment_id: str, status: str):
    conn = get_db()
    row = conn.execute("SELECT * FROM payments WHERE payment_id = ?", (payment_id,)).fetchone()
    if row:
        conn.execute("UPDATE payments SET status = ? WHERE payment_id = ?", (status, payment_id))
        if status == "approved":
            plan = row["plan"]
            user_id = row["user_id"]
            if plan == "basico":
                add_coins(user_id, 150)
            elif plan == "premium":
                add_coins(user_id, 300)
                add_diamonds(user_id, 5)
            elif plan == "ultra":
                add_coins(user_id, 700)
                add_diamonds(user_id, 10)
        conn.commit()
    conn.close()
