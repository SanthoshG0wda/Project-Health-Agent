import sqlite3
import os
from pathlib import Path

DB_PATH = Path(os.environ.get("SQLITE_PATH", "/tmp/project-health.db"))


def get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            project_name TEXT,
            filepath TEXT,
            rag_status TEXT,
            summary TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT REFERENCES sessions(id) ON DELETE CASCADE,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()


def create_session(session_id, project_name, filepath, rag_status):
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO sessions (id, project_name, filepath, rag_status) VALUES (?, ?, ?, ?)",
        (session_id, project_name, filepath, rag_status),
    )
    conn.commit()
    conn.close()


def update_session_summary(session_id, summary):
    conn = get_conn()
    conn.execute("UPDATE sessions SET summary = ? WHERE id = ?", (summary, session_id))
    conn.commit()
    conn.close()


def add_message(session_id, role, content):
    conn = get_conn()
    conn.execute(
        "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
        (session_id, role, content),
    )
    conn.commit()
    conn.close()


def get_session(session_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_messages(session_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT role, content, created_at FROM messages WHERE session_id = ? ORDER BY id",
        (session_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_recent_sessions(limit=10):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM sessions ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_old_sessions(hours=24):
    import datetime
    cutoff = datetime.datetime.now() - datetime.timedelta(hours=hours)
    conn = get_conn()
    conn.execute(
        "DELETE FROM sessions WHERE created_at < ?", (cutoff.isoformat(),)
    )
    conn.commit()
    conn.close()
