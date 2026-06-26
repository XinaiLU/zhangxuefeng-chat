from __future__ import annotations

import streamlit as st

from src.llm import chat_stream, create_client
from src.prompt import build_system_prompt
from src.search import web_search
from src.config import ApiConfig, load_api_config

st.set_page_config(
    page_title="张雪峰 · 志愿顾问",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="collapsed",
)

EXAMPLES = [
    "我孩子今年高考，560 分，河南的，想学金融，你怎么看？",
    "本科双非，想考研到 985，值得吗？还是直接工作？",
    "AI 时代来了，你之前推荐的专业还靠谱吗？",
    "家里没钱，该不该为了理想去学艺术？",
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


def init_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown("### 关于")
        st.caption("高考志愿 / 考研 / 职业规划的 AI 对话演示")
        st.markdown("[zhangxuefeng-skill](https://github.com/XinaiLU/zhangxuefeng-skill)")
        st.caption("角色扮演基于公开言论推断，非张雪峰本人观点，仅供参考。")
        if st.button("清空对话", use_container_width=True):
            st.session_state.messages = []
            st.rerun()


def ensure_api_config() -> ApiConfig:
    config = load_api_config()
    if not config.api_key:
        st.error("服务暂未就绪，请稍后再试。")
        st.caption("（管理员：请在 `.streamlit/secrets.toml` 或 Streamlit Cloud Secrets 中配置 qwen 或 openai 节）")
        st.stop()
    return config


def main() -> None:
    init_state()
    config = ensure_api_config()
    render_sidebar()

    st.markdown(
        """
        <style>
        .block-container { padding-top: 1.5rem; }
        [data-testid="stChatMessage"] { border-radius: 12px; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("🎓 张雪峰 · 认知操作系统")
    st.caption("高考志愿 / 考研 / 职业规划 — 打开即用，直接开聊")

    with st.expander("💡 试试这些问题", expanded=False):
        for example in EXAMPLES:
            if st.button(example, key=f"ex-{hash(example)}"):
                st.session_state.pending_prompt = example
                st.rerun()

    for message in st.session_state.messages:
        avatar = "🎓" if message["role"] == "assistant" else "👤"
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

    prompt = st.chat_input("问问张雪峰：专业怎么选？考研值不值？")
    if "pending_prompt" in st.session_state:
        prompt = st.session_state.pop("pending_prompt")

    if not prompt:
        return

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    search_context = None
    if config.enable_search and needs_web_search(prompt):
        with st.status("张雪峰正在查数据…", expanded=False):
            search_context = web_search(f"{prompt} 2026 就业 薪资 录取", max_results=5)

    system_prompt = build_system_prompt(search_context)
    client = create_client(config.api_key, config.base_url)
    history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[:-1]]

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

    st.session_state.messages.append({"role": "assistant", "content": reply})


if __name__ == "__main__":
    main()
