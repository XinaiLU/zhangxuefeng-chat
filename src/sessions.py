from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

import streamlit as st

Message = dict[str, str]
Session = dict[str, Any]


def _now_label() -> str:
    return datetime.now().strftime("%m-%d %H:%M")


def _title_from_message(text: str, max_len: int = 18) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= max_len:
        return cleaned or "新对话"
    return cleaned[:max_len] + "…"


def _new_session() -> Session:
    return {
        "id": str(uuid.uuid4())[:8],
        "title": "新对话",
        "messages": [],
        "updated_at": _now_label(),
    }


def init_sessions() -> None:
    if "sessions" not in st.session_state:
        first = _new_session()
        st.session_state.sessions = {first["id"]: first}
        st.session_state.session_order = [first["id"]]
        st.session_state.current_session_id = first["id"]


def current_session() -> Session:
    init_sessions()
    sid = st.session_state.current_session_id
    return st.session_state.sessions[sid]


def current_messages() -> list[Message]:
    return current_session()["messages"]


def set_current_messages(messages: list[Message]) -> None:
    session = current_session()
    session["messages"] = messages
    session["updated_at"] = _now_label()
    st.session_state.sessions[session["id"]] = session


def create_session() -> str:
    init_sessions()
    session = _new_session()
    st.session_state.sessions[session["id"]] = session
    st.session_state.session_order.insert(0, session["id"])
    st.session_state.current_session_id = session["id"]
    return session["id"]


def switch_session(session_id: str) -> None:
    if session_id in st.session_state.sessions:
        st.session_state.current_session_id = session_id


def delete_session(session_id: str) -> None:
    init_sessions()
    if session_id not in st.session_state.sessions:
        return
    del st.session_state.sessions[session_id]
    st.session_state.session_order = [sid for sid in st.session_state.session_order if sid != session_id]
    if not st.session_state.session_order:
        create_session()
    elif st.session_state.current_session_id == session_id:
        st.session_state.current_session_id = st.session_state.session_order[0]


def touch_session_title(user_text: str) -> None:
    session = current_session()
    if session["title"] == "新对话" and user_text.strip():
        session["title"] = _title_from_message(user_text)
        st.session_state.sessions[session["id"]] = session


def bump_session_order(session_id: str) -> None:
    order = st.session_state.session_order
    if session_id in order:
        order.remove(session_id)
    order.insert(0, session_id)


def render_session_sidebar() -> None:
    init_sessions()
    with st.sidebar:
        st.markdown("### 💬 对话记录")
        if st.button("➕ 新对话", use_container_width=True, type="primary"):
            create_session()
            st.rerun()

        st.divider()

        for sid in st.session_state.session_order:
            session = st.session_state.sessions[sid]
            is_active = sid == st.session_state.current_session_id
            label = session["title"]
            time_label = session.get("updated_at", "")
            rounds = len(session.get("messages", [])) // 2
            btn_label = f"{label}\n{time_label} · {rounds}轮"

            col_main, col_del = st.columns([5, 1])
            with col_main:
                btn_type = "primary" if is_active else "secondary"
                if st.button(
                    btn_label,
                    key=f"session-{sid}",
                    use_container_width=True,
                    type=btn_type,
                ):
                    switch_session(sid)
                    st.rerun()
            with col_del:
                if st.button("🗑", key=f"del-{sid}", help="删除此对话"):
                    delete_session(sid)
                    st.rerun()

        st.divider()
        st.caption("对话记录保存在当前浏览器会话中，刷新页面后仍会保留。")
        st.markdown("[zhangxuefeng-skill](https://github.com/XinaiLU/zhangxuefeng-skill)")
        st.caption("角色扮演仅供参考，非张雪峰本人观点。")
