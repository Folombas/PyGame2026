"""SQLite хранилище транзакций."""
import os
import sqlite3
from datetime import datetime


DB_DIR = os.path.expanduser("~/.bunny_budget")
DB_PATH = os.path.join(DB_DIR, "budget.db")


class Storage:
    def __init__(self, path=DB_PATH):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS transactions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                date        TEXT NOT NULL,
                amount      REAL NOT NULL,
                category    TEXT NOT NULL,
                description TEXT NOT NULL,
                kind        TEXT NOT NULL CHECK(kind IN ('spend','earn')),
                created_at  TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_date ON transactions(date);
            CREATE INDEX IF NOT EXISTS idx_cat  ON transactions(category);
        """)
        self.conn.commit()

    def add(self, amount, description, category, kind, date=None):
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        cur = self.conn.execute(
            "INSERT INTO transactions (date, amount, category, description, kind, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (date, abs(amount), category, description, kind,
             datetime.now().isoformat())
        )
        self.conn.commit()
        return cur.lastrowid

    def list(self, limit=20):
        cur = self.conn.execute(
            "SELECT * FROM transactions ORDER BY date DESC, id DESC LIMIT ?",
            (limit,)
        )
        return [dict(r) for r in cur.fetchall()]

    def delete(self, tx_id):
        cur = self.conn.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
        self.conn.commit()
        return cur.rowcount > 0

    def month(self, year, month):
        """Все транзакции за месяц."""
        prefix = f"{year:04d}-{month:02d}-"
        cur = self.conn.execute(
            "SELECT * FROM transactions WHERE date LIKE ? ORDER BY date",
            (prefix + "%",)
        )
        return [dict(r) for r in cur.fetchall()]

    def all(self):
        cur = self.conn.execute("SELECT * FROM transactions ORDER BY date")
        return [dict(r) for r in cur.fetchall()]

    def months(self):
        """Список всех месяцев в БД."""
        cur = self.conn.execute(
            "SELECT DISTINCT substr(date, 1, 7) as m FROM transactions ORDER BY m DESC"
        )
        return [r["m"] for r in cur.fetchall()]

    def close(self):
        self.conn.close()
