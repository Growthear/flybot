import sqlite3
from datetime import datetime, date

DB_PATH = "prices.db"


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS prices (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                departure_date TEXT NOT NULL,
                price_ars     REAL NOT NULL,
                checked_at    TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS alerts_sent (
                departure_date TEXT NOT NULL,
                sent_on        TEXT NOT NULL,
                PRIMARY KEY (departure_date, sent_on)
            )
        """)


def save_price(departure_date: str, price: float):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO prices (departure_date, price_ars, checked_at) VALUES (?, ?, ?)",
            (departure_date, price, datetime.utcnow().isoformat()),
        )


def get_average_price(departure_date: str) -> float | None:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT AVG(price_ars) FROM prices WHERE departure_date = ?",
            (departure_date,),
        ).fetchone()
    return row[0] if row and row[0] is not None else None


def already_alerted_today(departure_date: str) -> bool:
    today = date.today().isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT 1 FROM alerts_sent WHERE departure_date = ? AND sent_on = ?",
            (departure_date, today),
        ).fetchone()
    return row is not None


def mark_alert_sent(departure_date: str):
    today = date.today().isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO alerts_sent (departure_date, sent_on) VALUES (?, ?)",
            (departure_date, today),
        )
