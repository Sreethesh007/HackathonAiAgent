"""
Conversation persistence layer — SQLite via Python built-in sqlite3.

Schema
------
conversations
  id          INTEGER PK AUTOINCREMENT
  session_id  TEXT    NOT NULL  (UUID of the triage session)
  user_id     TEXT    NOT NULL  (JWT subject / patient identifier)
  role        TEXT    NOT NULL  CHECK(role IN ('user','assistant'))
  message     TEXT    NOT NULL
  timestamp   TEXT    NOT NULL  DEFAULT (datetime('now'))

Usage
-----
  from src.api.conversation_store import init_db, save_message, get_messages

  init_db()                                     # once at startup
  save_message(session_id, user_id, role, msg)  # persist a turn
  rows = get_messages(session_id)               # fetch history
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Literal

# ── Database path ────────────────────────────────────────────────────────────
# Stored in the project-level data/ directory (portable, relative to CWD).
_DB_PATH = Path("data") / "conversations.db"

# ── Internal helpers ─────────────────────────────────────────────────────────

def _connect() -> sqlite3.Connection:
    """Open (or create) the SQLite database file and return a connection.

    check_same_thread=False is safe here because every FastAPI request runs
    in its own async task and we keep connections short-lived (open → use → close).
    """
    conn = sqlite3.connect(str(_DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row        # rows behave like dicts
    conn.execute("PRAGMA journal_mode=WAL")  # better concurrent read performance
    return conn


# ── Public API ───────────────────────────────────────────────────────────────

def init_db(db_path: str | Path | None = None) -> None:
    """Create the database file and table if they do not already exist.

    Call once during application startup (inside the FastAPI lifespan handler).

    Args:
        db_path: Override the default ``data/conversations.db`` path.
                 Useful for tests or alternative deployment layouts.
    """
    global _DB_PATH
    if db_path is not None:
        _DB_PATH = Path(db_path)

    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with _connect() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS conversations (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id  TEXT    NOT NULL,
                user_id     TEXT    NOT NULL,
                role        TEXT    NOT NULL CHECK(role IN ('user', 'assistant')),
                message     TEXT    NOT NULL,
                timestamp   TEXT    NOT NULL DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_conv_session
                ON conversations(session_id);
            CREATE INDEX IF NOT EXISTS idx_conv_user
                ON conversations(user_id);
        """)


def save_message(
    session_id: str,
    user_id: str,
    role: Literal["user", "assistant"],
    message: str,
) -> int:
    """Persist a single conversation turn and return the new row id.

    Args:
        session_id: The triage session UUID.
        user_id:    The patient/user identifier (JWT subject).
        role:       ``"user"`` or ``"assistant"``.
        message:    The raw text content of the message.

    Returns:
        The auto-incremented ``id`` of the inserted row.
    """
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO conversations (session_id, user_id, role, message)
            VALUES (?, ?, ?, ?)
            """,
            (session_id, user_id, role, message),
        )
        return cur.lastrowid or 0


def get_messages(session_id: str) -> list[dict]:
    """Fetch all conversation turns for a session, ordered by timestamp.

    Args:
        session_id: The triage session UUID.

    Returns:
        A list of dicts with keys: id, session_id, user_id, role, message, timestamp.
    """
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT id, session_id, user_id, role, message, timestamp
            FROM   conversations
            WHERE  session_id = ?
            ORDER  BY timestamp ASC, id ASC
            """,
            (session_id,),
        ).fetchall()
        return [dict(row) for row in rows]


def delete_session(session_id: str) -> int:
    """Remove all messages for a session (useful for tests / GDPR purge).

    Returns:
        Number of rows deleted.
    """
    with _connect() as conn:
        cur = conn.execute(
            "DELETE FROM conversations WHERE session_id = ?",
            (session_id,),
        )
        return cur.rowcount
