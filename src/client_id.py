from __future__ import annotations

import uuid
from datetime import datetime, timedelta

import streamlit as st
from extra_streamlit_components import CookieManager

COOKIE_NAME = "zxf_cid"
COOKIE_DAYS = 365


@st.cache_resource
def _cookie_manager() -> CookieManager:
    return CookieManager()


def ensure_client_id() -> str:
    if st.session_state.get("client_id"):
        return st.session_state.client_id

    manager = _cookie_manager()
    cookies = manager.get_all()
    if cookies is None:
        st.stop()

    client_id = cookies.get(COOKIE_NAME)
    if not client_id:
        client_id = str(uuid.uuid4())
        manager.set(
            COOKIE_NAME,
            client_id,
            expires_at=datetime.now() + timedelta(days=COOKIE_DAYS),
        )
        st.session_state.client_id = client_id
        st.rerun()

    st.session_state.client_id = client_id
    return client_id
