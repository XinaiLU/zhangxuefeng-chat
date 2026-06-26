from __future__ import annotations

import streamlit as st

from src.config import ApiConfig, load_api_config
from src.llm import chat_stream, create_client
from src.prompt import build_system_prompt
from src.search import web_search
from src.sessions import (
    bump_session_order,
    current_messages,
    init_sessions,
    render_session_sidebar,
    set_current_messages,
    touch_session_title,
)
from src.ui import inject_styles, render_hero

st.set_page_config(
    page_title="对话张雪峰",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

EXAMPLES = [
    "我孩子今年高考，560 分，河南的，想学金融，你怎么看？",
    "本科双非，想考研到 985，值得吗？还是直接工作？",
    "AI 时代来了，你之前推荐的专业还靠谱吗？",
]

NEEDS_SEARCH_HINTS = (
    "专业",
    "院校",
    "学校",
    "就业",
    "薪资",
    "考研",
    "高考",
    "志愿",
    "行业",
    "分数",
    "录取",
    "AI",
    "人工智能",
    "金融",
    "计算机",
)


def needs_web_search(text: str) -> bool:
    lowered = text.lower()
    return any(kw.lower() in lowered for kw in NEEDS_SEARCH_HINTS)


def ensure_api_config() -> ApiConfig:
    config = load_api_config()
    if not config.api_key:
        st.error("服务暂未就绪，请稍后再试。")
        st.caption("（管理员：请在 `.streamlit/secrets.toml` 或 Streamlit Cloud Secrets 中配置 qwen 或 openai 节）")
        st.stop()
    return config


def main() -> None:
    init_sessions()
    config = ensure_api_config()
    inject_styles()
    render_session_sidebar()

    messages = current_messages()
    render_hero()

    with st.expander("💡 试试这些问题", expanded=not messages):
        for example in EXAMPLES:
            if st.button(example, key=f"ex-{hash(example)}", use_container_width=True):
                st.session_state.pending_prompt = example
                st.rerun()

    for message in messages:
        avatar = "🎓" if message["role"] == "assistant" else "👤"
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

    prompt = st.chat_input("问问张雪峰：专业怎么选？考研值不值？")
    if "pending_prompt" in st.session_state:
        prompt = st.session_state.pop("pending_prompt")

    if not prompt:
        return

    touch_session_title(prompt)
    messages = [*messages, {"role": "user", "content": prompt}]
    set_current_messages(messages)
    bump_session_order(st.session_state.current_session_id)

    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    search_context = None
    if config.enable_search and needs_web_search(prompt):
        with st.status("张雪峰正在查数据…", expanded=False):
            search_context = web_search(f"{prompt} 2026 就业 薪资 录取", max_results=5)

    system_prompt = build_system_prompt(search_context)
    client = create_client(config.api_key, config.base_url)
    history = [{"role": m["role"], "content": m["content"]} for m in messages[:-1]]

    with st.chat_message("assistant", avatar="🎓"):
        placeholder = st.empty()
        try:
            chunks: list[str] = []
            for piece in chat_stream(
                client,
                model=config.model,
                system_prompt=system_prompt,
                messages=[*history, {"role": "user", "content": prompt}],
            ):
                chunks.append(piece)
                placeholder.markdown("".join(chunks))
            reply = "".join(chunks)
        except Exception as exc:
            st.error("回复生成失败，请稍后重试。")
            st.caption(f"详情: {exc}")
            return

    set_current_messages([*messages, {"role": "assistant", "content": reply}])


if __name__ == "__main__":
    main()
