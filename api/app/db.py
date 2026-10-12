import sqlite3
from contextlib import contextmanager
from pathlib import Path

from .config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS tickets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  source TEXT, sender TEXT, subject TEXT, message TEXT NOT NULL,
  category TEXT, priority TEXT, sentiment TEXT,
  summary TEXT, suggested_reply TEXT, kb_sources TEXT, provider TEXT
);
"""

_GROUPABLE = {"category", "priority", "sentiment"}


@contextmanager
def conn():
    path = Path(settings.db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(path)
    c.row_factory = sqlite3.Row
    c.executescript(SCHEMA)
    try:
        yield c
        c.commit()
    finally:
        c.close()


def insert_ticket(row: dict) -> int:
    with conn() as c:
        cur = c.execute(
            """INSERT INTO tickets (source, sender, subject, message, category, priority,
               sentiment, summary, suggested_reply, kb_sources, provider)
               VALUES (:source, :sender, :subject, :message, :category, :priority,
               :sentiment, :summary, :suggested_reply, :kb_sources, :provider)""",
            row,
        )
        return cur.lastrowid


def list_tickets(limit: int = 50, priority: "str | None" = None) -> list[dict]:
    q, args = "SELECT * FROM tickets", []
    if priority:
        q += " WHERE priority = ?"
        args.append(priority)
    q += " ORDER BY id DESC LIMIT ?"
    args.append(limit)
    with conn() as c:
        return [dict(r) for r in c.execute(q, args)]


def stats() -> dict:
    with conn() as c:
        total = c.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
        today = c.execute(
            "SELECT COUNT(*) FROM tickets WHERE date(created_at) = date('now')"
        ).fetchone()[0]

        def by(col: str) -> dict:
            assert col in _GROUPABLE
            return {r[0]: r[1] for r in c.execute(
                f"SELECT {col}, COUNT(*) FROM tickets GROUP BY {col}")}

        return {
            "total": total,
            "today": today,
            "by_category": by("category"),
            "by_priority": by("priority"),
            "by_sentiment": by("sentiment"),
        }
