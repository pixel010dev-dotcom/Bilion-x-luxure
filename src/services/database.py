"""Database module for Bilion Luxure - SQLite com tracking financeiro."""
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
            plan TEXT DEFAULT 'free',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount_gross REAL DEFAULT 0,
            amount_net REAL DEFAULT 0,
            mp_fee REAL DEFAULT 0,
            payment_id TEXT,
            status TEXT DEFAULT 'pending',
            plan TEXT,
            coins_delivered INTEGER DEFAULT 0,
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

        CREATE TABLE IF NOT EXISTS financial_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            description TEXT,
            amount_gross REAL DEFAULT 0,
            amount_net REAL DEFAULT 0,
            mp_fee REAL DEFAULT 0,
            gen_cost REAL DEFAULT 0,
            profit REAL DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Migração: remover coluna diamonds se existir (SQLite não dropa fácil)
    # Só ignoramos ela — não usamos mais
    conn.commit()
    conn.close()


# ─── USERS ───

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


# ─── GENERATIONS ───

def save_generation(user_id: int, gen_type: str, prompt: str, cost: int, result_url: str = None):
    conn = get_db()
    conn.execute(
        "INSERT INTO generations (user_id, type, prompt, cost, result_url) VALUES (?, ?, ?, ?, ?)",
        (user_id, gen_type, prompt, cost, result_url),
    )
    conn.commit()
    conn.close()


# ─── PAYMENTS ───

def create_payment(user_id: int, amount_gross: float, amount_net: float, payment_id: str, plan: str, coins: int):
    mp_fee = round(amount_gross - amount_net, 2)
    conn = get_db()
    conn.execute(
        "INSERT INTO payments (user_id, amount_gross, amount_net, mp_fee, payment_id, plan, coins_delivered) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (user_id, amount_gross, amount_net, mp_fee, payment_id, plan, coins),
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
            coins = row["coins_delivered"]
            # Tudo na mesma conexão pra evitar lock
            conn.execute("UPDATE users SET coins = coins + ? WHERE user_id = ?", (coins, user_id))
            mp_fee = row["mp_fee"]
            profit = round(row["amount_net"], 2)
            conn.execute(
                "INSERT INTO financial_log (type, description, amount_gross, amount_net, mp_fee, profit) VALUES (?, ?, ?, ?, ?, ?)",
                ("venda", f"Plano {plan} - User {user_id}", row["amount_gross"], row["amount_net"], mp_fee, profit),
            )
        conn.commit()
    conn.close()


# ─── FINANCIAL LOG ───

def log_financial(type: str, description: str, amount_gross: float = 0, amount_net: float = 0, mp_fee: float = 0, gen_cost: float = 0):
    profit = round(amount_net - gen_cost, 2) if gen_cost else round(amount_net, 2)
    conn = get_db()
    conn.execute(
        "INSERT INTO financial_log (type, description, amount_gross, amount_net, mp_fee, gen_cost, profit) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (type, description, amount_gross, amount_net, mp_fee, gen_cost, profit),
    )
    conn.commit()
    conn.close()


def get_financial_summary() -> dict:
    """Retorna resumo financeiro completo."""
    conn = get_db()
    total_vendas = conn.execute(
        "SELECT COUNT(*) as count, COALESCE(SUM(amount_gross), 0) as gross, COALESCE(SUM(amount_net), 0) as net, COALESCE(SUM(mp_fee), 0) as fees FROM payments WHERE status = 'approved'"
    ).fetchone()

    total_gen = conn.execute(
        "SELECT COUNT(*) as count, COALESCE(SUM(cost), 0) as total_coins_spent FROM generations"
    ).fetchone()

    total_coins_emitidas = conn.execute(
        "SELECT COALESCE(SUM(coins_delivered), 0) as coins FROM payments WHERE status = 'approved'"
    ).fetchone()

    conn.close()

    v = dict(total_vendas)
    g = dict(total_gen)
    coins = dict(total_coins_emitidas)

    # Custo real de geração (cada coin gasto = R$0,011 se foi imagem)
    gen_cost_real = round(g["total_coins_spent"] * 0.011, 2)

    return {
        "vendas": {
            "total": v["count"],
            "bruto": round(v["gross"], 2),
            "liquido": round(v["net"], 2),
            "taxas_mp": round(v["fees"], 2),
        },
        "geracoes": {
            "total": g["count"],
            "coins_gastos": g["total_coins_spent"],
            "custo_real": gen_cost_real,
        },
        "lucro_estimado": round(v["net"] - gen_cost_real, 2),
        "coins_emitidas": coins["coins"],
    }
