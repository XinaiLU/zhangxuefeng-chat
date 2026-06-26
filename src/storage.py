from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator, Optional

Message = dict[str, str]
Session = dict[str, Any]

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "conversations.db"


def _now_label() -> str:
    return datetime.now().strftime("%m-%d %H:%M")


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


@contextmanager
def _connect() -> Iterator[sqlite3.Connection]:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS clients (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS chat_sessions (
                id TEXT PRIMARY KEY,
                client_id TEXT NOT NULL,
                title TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                sort_rank INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                sort_order INTEGER NOT NULL,
                FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS client_state (
                client_id TEXT PRIMARY KEY,
                current_session_id TEXT,
                FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
            );
            """
        )


def ensure_client(client_id: str) -> None:
    init_db()
    with _connect() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO clients (id, created_at) VALUES (?, ?)",
            (client_id, _now_iso()),
        )


def load_client_data(client_id: str) -> tuple[dict[str, Session], list[str], Optional[str]]:
    init_db()
    ensure_client(client_id)
    sessions: dict[str, Session] = {}
    order: list[str] = []

    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT id, title, updated_at
            FROM chat_sessions
            WHERE client_id = ?
            ORDER BY sort_rank ASC, updated_at DESC
            """,
            (client_id,),
        ).fetchall()

        for row in rows:
            sid = row["id"]
            messages = conn.execute(
                """
                SELECT role, content
                FROM chat_messages
                WHERE session_id = ?
                ORDER BY sort_order ASC
                """,
                (sid,),
            ).fetchall()
            sessions[sid] = {
                "id": sid,
                "title": row["title"],
                "updated_at": row["updated_at"],
                "messages": [{"role": m["role"], "content": m["content"]} for m in messages],
            }
            order.append(sid)

        state = conn.execute(
            "SELECT current_session_id FROM client_state WHERE client_id = ?",
            (client_id,),
        ).fetchone()
        current_id = state["current_session_id"] if state else None

    if current_id and current_id not in sessions:
        current_id = order[0] if order else None

    return sessions, order, current_id


def save_session(client_id: str, session: Session, sort_rank: int) -> None:
    init_db()
    ensure_client(client_id)
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO chat_sessions (id, client_id, title, updated_at, sort_rank)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title = excluded.title,
                updated_at = excluded.updated_at,
                sort_rank = excluded.sort_rank
            """,
            (session["id"], client_id, session["title"], session["updated_at"], sort_rank),
        )


def save_messages(session_id: str, messages: list[Message]) -> None:
    init_db()
    with _connect() as conn:
        conn.execute("DELETE FROM chat_messages WHERE session_id = ?", (session_id,))
        conn.executemany(
            "INSERT INTO chat_messages (session_id, role, content, sort_order) VALUES (?, ?, ?, ?)",
            [(session_id, m["role"], m["content"], idx) for idx, m in enumerate(messages)],
        )


def save_session_order(client_id: str, session_order: list[str]) -> None:
    init_db()
    with _connect() as conn:
        for rank, sid in enumerate(session_order):
            conn.execute(
                "UPDATE chat_sessions SET sort_rank = ? WHERE id = ? AND client_id = ?",
                (rank, sid, client_id),
            )


def set_current_session(client_id: str, session_id: str) -> None:
    init_db()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO client_state (client_id, current_session_id)
            VALUES (?, ?)
            ON CONFLICT(client_id) DO UPDATE SET current_session_id = excluded.current_session_id
            """,
            (client_id, session_id),
        )


def delete_session_db(client_id: str, session_id: str) -> None:
    init_db()
    with _connect() as conn:
        conn.execute(
            "DELETE FROM chat_sessions WHERE id = ? AND client_id = ?",
            (session_id, client_id),
        )


def persist_session(client_id: str, session: Session, session_order: list[str]) -> None:
    rank = session_order.index(session["id"]) if session["id"] in session_order else 0
    save_session(client_id, session, rank)
    save_messages(session["id"], session["messages"])
    save_session_order(client_id, session_order)
