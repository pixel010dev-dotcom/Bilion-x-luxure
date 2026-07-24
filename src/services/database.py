"""
Database module for Bilion Luxure.
Suporta SQLite (local dev) e PostgreSQL (Railway).
Detecta automaticamente pelo prefixo da DATABASE_URL.
"""

import os
import sqlite3
from datetime import datetime

DB_PATH = os.environ.get("DATABASE_URL", "data/bilion.db")
IS_POSTGRES = DB_PATH.startswith("postgresql://")


# ─── Conexão ───

def get_db():
    if IS_POSTGRES:
        import psycopg2
        conn = psycopg2.connect(DB_PATH)
        conn.autocommit = False
        return conn
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _fetchone(conn, sql, params=()):
    """Retorna uma linha como dict (compatível SQLite/Postgres)."""
    if IS_POSTGRES:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
            if row:
                desc = [d[0] for d in cur.description]
                return dict(zip(desc, row))
            return None
    row = conn.execute(sql, params).fetchone()
    return dict(row) if row else None


def _fetchall(conn, sql, params=()):
    """Retorna lista de dicts."""
    if IS_POSTGRES:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
            if not rows:
                return []
            desc = [d[0] for d in cur.description]
            return [dict(zip(desc, r)) for r in rows]
    rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def _execute(conn, sql, params=()):
    """Executa e retorna cursor (Postgres faz commit depois)."""
    if IS_POSTGRES:
        cur = conn.cursor()
        cur.execute(sql, params)
        return cur
    return conn.execute(sql, params)


# ─── Init ───

def init_db():
    conn = get_db()
    if IS_POSTGRES:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                coins INTEGER DEFAULT 0,
                plan TEXT DEFAULT 'free',
                tos_accepted INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(user_id),
                amount_gross REAL DEFAULT 0,
                amount_net REAL DEFAULT 0,
                mp_fee REAL DEFAULT 0,
                payment_id TEXT,
                status TEXT DEFAULT 'pending',
                plan TEXT,
                coins_delivered INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS generations (
                id SERIAL PRIMARY KEY,
                user_id BIGINT REFERENCES users(user_id),
                type TEXT,
                prompt TEXT,
                cost INTEGER,
                result_url TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS financial_log (
                id SERIAL PRIMARY KEY,
                type TEXT,
                description TEXT,
                amount_gross REAL DEFAULT 0,
                amount_net REAL DEFAULT 0,
                mp_fee REAL DEFAULT 0,
                gen_cost REAL DEFAULT 0,
                profit REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        conn.commit()
        cur.close()
    else:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                coins INTEGER DEFAULT 0,
                plan TEXT DEFAULT 'free',
                tos_accepted INTEGER DEFAULT 0,
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
    conn.commit()
    # Migracao: adiciona tos_accepted em tabelas antigas
    if IS_POSTGRES:
        try:
            _execute(conn, "ALTER TABLE users ADD COLUMN IF NOT EXISTS tos_accepted INTEGER DEFAULT 0")
            conn.commit()
        except Exception:
            conn.rollback()
    else:
        cur = _execute(conn, "PRAGMA table_info(users)")
        cols = [row[1] for row in cur.fetchall()]
        if "tos_accepted" not in cols:
            _execute(conn, "ALTER TABLE users ADD COLUMN tos_accepted INTEGER DEFAULT 0")
            conn.commit()

    conn.close()


# ─── USERS ───

def get_user(user_id: int):
    conn = get_db()
    row = _fetchone(conn, "SELECT * FROM users WHERE user_id = %s" if IS_POSTGRES else "SELECT * FROM users WHERE user_id = ?", (user_id,))
    conn.close()
    return row


def create_user(user_id: int, username: str = None, first_name: str = None):
    conn = get_db()
    if IS_POSTGRES:
        _execute(conn,
            "INSERT INTO users (user_id, username, first_name) VALUES (%s, %s, %s) ON CONFLICT (user_id) DO NOTHING",
            (user_id, username, first_name))
    else:
        _execute(conn,
            "INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
            (user_id, username, first_name))
    conn.commit()
    conn.close()


def accept_tos(user_id: int):
    """Marca os termos como aceitos."""
    conn = get_db()
    _execute(conn,
        "UPDATE users SET tos_accepted = 1 WHERE user_id = %s" if IS_POSTGRES else "UPDATE users SET tos_accepted = 1 WHERE user_id = ?",
        (user_id,))
    conn.commit()
    conn.close()


def add_coins(user_id: int, amount: int):
    conn = get_db()
    _execute(conn,
        "UPDATE users SET coins = coins + %s WHERE user_id = %s" if IS_POSTGRES else "UPDATE users SET coins = coins + ? WHERE user_id = ?",
        (amount, user_id))
    conn.commit()
    conn.close()


def spend_coins(user_id: int, amount: int) -> bool:
    conn = get_db()
    row = _fetchone(conn,
        "SELECT coins FROM users WHERE user_id = %s" if IS_POSTGRES else "SELECT coins FROM users WHERE user_id = ?",
        (user_id,))
    if row and row["coins"] >= amount:
        _execute(conn,
            "UPDATE users SET coins = coins - %s WHERE user_id = %s" if IS_POSTGRES else "UPDATE users SET coins = coins - ? WHERE user_id = ?",
            (amount, user_id))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False


# ─── GENERATIONS ───

def save_generation(user_id: int, gen_type: str, prompt: str, cost: int, result_url: str = None):
    conn = get_db()
    _execute(conn,
        "INSERT INTO generations (user_id, type, prompt, cost, result_url) VALUES (%s, %s, %s, %s, %s)" if IS_POSTGRES
        else "INSERT INTO generations (user_id, type, prompt, cost, result_url) VALUES (?, ?, ?, ?, ?)",
        (user_id, gen_type, prompt, cost, result_url))
    conn.commit()
    conn.close()


# ─── PAYMENTS ───

def create_payment(user_id: int, amount_gross: float, amount_net: float, payment_id: str, plan: str, coins: int):
    mp_fee = round(amount_gross - amount_net, 2)
    conn = get_db()
    _execute(conn,
        "INSERT INTO payments (user_id, amount_gross, amount_net, mp_fee, payment_id, plan, coins_delivered) VALUES (%s, %s, %s, %s, %s, %s, %s)" if IS_POSTGRES
        else "INSERT INTO payments (user_id, amount_gross, amount_net, mp_fee, payment_id, plan, coins_delivered) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (user_id, amount_gross, amount_net, mp_fee, payment_id, plan, coins))
    conn.commit()
    conn.close()


def update_payment_status(payment_id: str, status: str):
    conn = get_db()
    row = _fetchone(conn,
        "SELECT * FROM payments WHERE payment_id = %s" if IS_POSTGRES else "SELECT * FROM payments WHERE payment_id = ?",
        (payment_id,))
    if row:
        # Já aprovado — ignora pra não somar coins de novo
        if row["status"] == "approved":
            conn.close()
            return
        _execute(conn,
            "UPDATE payments SET status = %s WHERE payment_id = %s" if IS_POSTGRES else "UPDATE payments SET status = ? WHERE payment_id = ?",
            (status, payment_id))
        if status == "approved":
            plan = row["plan"]
            user_id = row["user_id"]
            coins = row["coins_delivered"]
            _execute(conn,
                "UPDATE users SET coins = coins + %s WHERE user_id = %s" if IS_POSTGRES else "UPDATE users SET coins = coins + ? WHERE user_id = ?",
                (coins, user_id))
            mp_fee = row["mp_fee"]
            profit = round(row["amount_net"], 2)
            _execute(conn,
                "INSERT INTO financial_log (type, description, amount_gross, amount_net, mp_fee, profit) VALUES (%s, %s, %s, %s, %s, %s)" if IS_POSTGRES
                else "INSERT INTO financial_log (type, description, amount_gross, amount_net, mp_fee, profit) VALUES (?, ?, ?, ?, ?, ?)",
                ("venda", f"Plano {plan} - User {user_id}", row["amount_gross"], row["amount_net"], mp_fee, profit))
        conn.commit()
    conn.close()


# ─── FINANCIAL LOG ───

def log_financial(type: str, description: str, amount_gross: float = 0, amount_net: float = 0, mp_fee: float = 0, gen_cost: float = 0):
    profit = round(amount_net - gen_cost, 2) if gen_cost else round(amount_net, 2)
    conn = get_db()
    _execute(conn,
        "INSERT INTO financial_log (type, description, amount_gross, amount_net, mp_fee, gen_cost, profit) VALUES (%s, %s, %s, %s, %s, %s, %s)" if IS_POSTGRES
        else "INSERT INTO financial_log (type, description, amount_gross, amount_net, mp_fee, gen_cost, profit) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (type, description, amount_gross, amount_net, mp_fee, gen_cost, profit))
    conn.commit()
    conn.close()


def get_financial_summary() -> dict:
    """Retorna resumo financeiro completo."""
    conn = get_db()
    PH = "%s" if IS_POSTGRES else "?"

    v = _fetchone(conn,
        "SELECT COUNT(*) as count, COALESCE(SUM(amount_gross), 0) as gross, COALESCE(SUM(amount_net), 0) as net, COALESCE(SUM(mp_fee), 0) as fees FROM payments WHERE status = 'approved'")

    g = _fetchone(conn,
        "SELECT COUNT(*) as count, COALESCE(SUM(cost), 0) as total_coins_spent FROM generations")

    coins = _fetchone(conn,
        "SELECT COALESCE(SUM(coins_delivered), 0) as coins FROM payments WHERE status = 'approved'")

    conn.close()

    if not v:
        v = {"count": 0, "gross": 0, "net": 0, "fees": 0}
    if not g:
        g = {"count": 0, "total_coins_spent": 0}
    if not coins:
        coins = {"coins": 0}

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
