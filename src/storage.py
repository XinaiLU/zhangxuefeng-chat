from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

Message = dict[str, str]
Session = dict[str, Any]

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SESSIONS_CSV = DATA_DIR / "sessions.csv"
MESSAGES_CSV = DATA_DIR / "messages.csv"
STATE_CSV = DATA_DIR / "client_state.csv"

SESSION_FIELDS = ["client_id", "session_id", "title", "updated_at", "sort_rank"]
MESSAGE_FIELDS = ["client_id", "session_id", "sort_order", "role", "content"]
STATE_FIELDS = ["client_id", "current_session_id"]


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _read_csv(path: Path, fields: list[str]) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows: list[dict[str, str]] = []
        for row in reader:
            rows.append({field: row.get(field, "") for field in fields})
        return rows


def _write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(rows)


def init_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for path, fields in (
        (SESSIONS_CSV, SESSION_FIELDS),
        (MESSAGES_CSV, MESSAGE_FIELDS),
        (STATE_CSV, STATE_FIELDS),
    ):
        if not path.exists():
            _write_csv(path, fields, [])


def ensure_client(client_id: str) -> None:
    init_db()
    states = _read_csv(STATE_CSV, STATE_FIELDS)
    if not any(row["client_id"] == client_id for row in states):
        states.append({"client_id": client_id, "current_session_id": ""})
        _write_csv(STATE_CSV, STATE_FIELDS, states)


def load_client_data(client_id: str) -> tuple[dict[str, Session], list[str], Optional[str]]:
    init_db()
    ensure_client(client_id)

    session_rows = [
        row for row in _read_csv(SESSIONS_CSV, SESSION_FIELDS) if row["client_id"] == client_id
    ]
    session_rows.sort(key=lambda row: (int(row["sort_rank"]), row["updated_at"]), reverse=False)

    message_rows = [
        row for row in _read_csv(MESSAGES_CSV, MESSAGE_FIELDS) if row["client_id"] == client_id
    ]
    messages_by_session: dict[str, list[Message]] = {}
    for row in sorted(message_rows, key=lambda item: int(item["sort_order"])):
        messages_by_session.setdefault(row["session_id"], []).append(
            {"role": row["role"], "content": row["content"]}
        )

    sessions: dict[str, Session] = {}
    order: list[str] = []
    for row in session_rows:
        sid = row["session_id"]
        sessions[sid] = {
            "id": sid,
            "title": row["title"],
            "updated_at": row["updated_at"],
            "messages": messages_by_session.get(sid, []),
        }
        order.append(sid)

    current_id: Optional[str] = None
    for row in _read_csv(STATE_CSV, STATE_FIELDS):
        if row["client_id"] == client_id:
            current_id = row["current_session_id"] or None
            break

    if current_id and current_id not in sessions:
        current_id = order[0] if order else None

    return sessions, order, current_id


def save_session(client_id: str, session: Session, sort_rank: int) -> None:
    init_db()
    ensure_client(client_id)
    rows = [row for row in _read_csv(SESSIONS_CSV, SESSION_FIELDS) if row["session_id"] != session["id"]]
    rows.append(
        {
            "client_id": client_id,
            "session_id": session["id"],
            "title": session["title"],
            "updated_at": session["updated_at"],
            "sort_rank": str(sort_rank),
        }
    )
    _write_csv(SESSIONS_CSV, SESSION_FIELDS, rows)


def save_messages(client_id: str, session_id: str, messages: list[Message]) -> None:
    init_db()
    rows = [
        row
        for row in _read_csv(MESSAGES_CSV, MESSAGE_FIELDS)
        if not (row["client_id"] == client_id and row["session_id"] == session_id)
    ]
    for idx, message in enumerate(messages):
        rows.append(
            {
                "client_id": client_id,
                "session_id": session_id,
                "sort_order": str(idx),
                "role": message["role"],
                "content": message["content"],
            }
        )
    _write_csv(MESSAGES_CSV, MESSAGE_FIELDS, rows)


def save_session_order(client_id: str, session_order: list[str]) -> None:
    init_db()
    rows = _read_csv(SESSIONS_CSV, SESSION_FIELDS)
    rank_map = {sid: rank for rank, sid in enumerate(session_order)}
    for row in rows:
        if row["client_id"] == client_id and row["session_id"] in rank_map:
            row["sort_rank"] = str(rank_map[row["session_id"]])
    _write_csv(SESSIONS_CSV, SESSION_FIELDS, rows)


def set_current_session(client_id: str, session_id: str) -> None:
    init_db()
    ensure_client(client_id)
    rows = _read_csv(STATE_CSV, STATE_FIELDS)
    found = False
    for row in rows:
        if row["client_id"] == client_id:
            row["current_session_id"] = session_id
            found = True
            break
    if not found:
        rows.append({"client_id": client_id, "current_session_id": session_id})
    _write_csv(STATE_CSV, STATE_FIELDS, rows)


def delete_session_db(client_id: str, session_id: str) -> None:
    init_db()
    sessions = [
        row
        for row in _read_csv(SESSIONS_CSV, SESSION_FIELDS)
        if not (row["client_id"] == client_id and row["session_id"] == session_id)
    ]
    messages = [
        row
        for row in _read_csv(MESSAGES_CSV, MESSAGE_FIELDS)
        if not (row["client_id"] == client_id and row["session_id"] == session_id)
    ]
    _write_csv(SESSIONS_CSV, SESSION_FIELDS, sessions)
    _write_csv(MESSAGES_CSV, MESSAGE_FIELDS, messages)


def persist_session(client_id: str, session: Session, session_order: list[str]) -> None:
    rank = session_order.index(session["id"]) if session["id"] in session_order else 0
    save_session(client_id, session, rank)
    save_messages(client_id, session["id"], session["messages"])
    save_session_order(client_id, session_order)
