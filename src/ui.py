from __future__ import annotations

import html

import streamlit as st

from src.config import ApiConfig, model_display_name, provider_display_name


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 1.5rem;
            max-width: 46rem;
        }

        .hero-wrap {
            margin-bottom: 1rem;
        }
        .hero-title {
            font-size: 2.5rem;
            font-weight: 900;
            line-height: 1.2;
            margin: 0;
            color: #000000;
            letter-spacing: 0.02em;
        }
        .hero-sub {
            margin: 0.6rem 0 0;
            color: #1a1a1a;
            font-size: 1.15rem;
            font-weight: 500;
            line-height: 1.5;
        }

        [data-testid="stChatMessage"] {
            border-radius: 14px;
            padding: 0.2rem 0;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #fafafa 0%, #f3f4f6 100%);
        }
        [data-testid="stSidebar"] .sidebar-title {
            font-size: 1rem;
            font-weight: 700;
            margin: 0 0 0.75rem;
            color: #111827;
        }

        [data-testid="stSidebar"] [data-testid="stButton"] button {
            border-radius: 10px;
            min-height: 3.1rem;
            padding: 0.45rem 0.65rem;
        }
        [data-testid="stSidebar"] [data-testid="stButton"] p {
            text-align: left;
            font-size: 0.8rem;
            line-height: 1.35;
            margin: 0;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        [data-testid="stSidebar"] [data-testid="stButton"] button[kind="primary"] {
            border: 1px solid #e11d48;
            background: #fff1f2;
            color: #9f1239;
        }
        [data-testid="stSidebar"] [data-testid="stButton"] button[kind="secondary"] {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            color: #374151;
        }

        .session-meta {
            font-size: 0.72rem;
            color: #9ca3af;
            margin: -0.35rem 0 0.55rem 0.15rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .session-meta.active {
            color: #be123c;
        }

        .model-info {
            font-size: 0.82rem;
            color: #374151;
            line-height: 1.55;
            margin: 0;
        }
        .model-info strong {
            color: #111827;
        }

        div[data-testid="stExpander"] {
            border: 1px solid #eceff3;
            border-radius: 12px;
            background: #fafbfc;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    st.markdown(
        """
        <div class="hero-wrap">
            <h1 class="hero-title">对话张雪峰</h1>
            <p class="hero-sub">——请为我生成一张雪峰的志愿</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_model_info(config: ApiConfig) -> None:
    search_text = "已开启（涉及专业/就业时会检索公开信息）" if config.enable_search else "已关闭"
    provider = html.escape(provider_display_name(config.provider))
    model_name = html.escape(model_display_name(config.model))
    model_id = html.escape(config.model)

    st.markdown(
        f"""
        <p class="model-info">
            <strong>基模</strong>：{model_name}<br>
            <strong>模型 ID</strong>：<code>{model_id}</code><br>
            <strong>提供商</strong>：{provider}<br>
            <strong>联网检索</strong>：{html.escape(search_text)}<br>
            <strong>角色 Skill</strong>：zhangxuefeng-skill
        </p>
        """,
        unsafe_allow_html=True,
    )


def render_session_meta(time_label: str, rounds: int, is_active: bool) -> None:
    css_class = "session-meta active" if is_active else "session-meta"
    st.markdown(
        f'<p class="{css_class}">{html.escape(time_label)} · {rounds} 轮</p>',
        unsafe_allow_html=True,
    )
