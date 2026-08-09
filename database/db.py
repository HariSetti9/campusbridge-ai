import json
import sqlite3
from datetime import datetime, timezone

from config import DB_PATH


def _connect():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = _connect()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS saved_opportunities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            organization TEXT,
            opportunity_type TEXT,
            deadline TEXT,
            summary TEXT,
            original_notice TEXT,
            analysis_json TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_opportunity(opportunity: dict, original_notice: str) -> int:
    conn = _connect()
    cur = conn.execute(
        """INSERT INTO saved_opportunities
           (title, organization, opportunity_type, deadline, summary,
            original_notice, analysis_json, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            opportunity.get("title", "Not specified"),
            opportunity.get("organization", "Not specified"),
            opportunity.get("opportunity_type", "Not specified"),
            opportunity.get("deadline", "Not specified"),
            opportunity.get("summary", ""),
            original_notice,
            json.dumps(opportunity),
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def list_saved_opportunities() -> list[dict]:
    conn = _connect()
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM saved_opportunities ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_opportunity(opportunity_id: int):
    conn = _connect()
    conn.execute("DELETE FROM saved_opportunities WHERE id = ?", (opportunity_id,))
    conn.commit()
    conn.close()
