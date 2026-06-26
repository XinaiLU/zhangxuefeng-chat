from __future__ import annotations

from typing import Optional

import streamlit as st

from src.llm import chat_stream, create_client
from src.prompt import build_system_prompt
from src.search import web_search

st.set_page_config(
    page_title="张雪峰 · 志愿顾问",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="expanded",
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


def build_qwen_base_url(workspace_id: str) -> str:
    ws = workspace_id.strip().removeprefix("https://").split(".")[0]
    return f"https://{ws}.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"


def get_secret(section: str, key: str, default: str = "") -> str:
    try:
        return str(st.secrets[section][key])
    except (KeyError, FileNotFoundError, AttributeError):
        return default


def render_sidebar() -> tuple[str, Optional[str], str, bool]:
    qwen_key = get_secret("qwen", "api_key")
    qwen_ws = get_secret("qwen", "workspace_id")
    qwen_model = get_secret("qwen", "model", "qwen-plus")
    openai_key = get_secret("openai", "api_key")
    openai_base = get_secret("openai", "base_url")
    openai_model = get_secret("openai", "model", "gpt-4o-mini")
    has_qwen_secrets = bool(qwen_key and qwen_ws)

    with st.sidebar:
        st.title("⚙️ 设置")
        default_provider = "通义千问 (Qwen)" if has_qwen_secrets else "OpenAI / 其他兼容接口"
        provider = st.selectbox("模型提供商", ["通义千问 (Qwen)", "OpenAI / 其他兼容接口"], index=0 if default_provider.startswith("通义") else 1)

        if provider.startswith("通义"):
            st.caption(
                "新版 Key 以 `sk-ws` 开头，需在百炼控制台 → "
                "[业务空间](https://bailian.console.aliyun.com/?tab=globalset#/workspace) 查看 Workspace ID"
            )
            api_key = st.text_input(
                "API Key",
                value=qwen_key,
                type="password",
                help="也可在 Streamlit Secrets 中配置 qwen.api_key",
            )
            workspace_id = st.text_input(
                "Workspace ID",
                value=qwen_ws,
                placeholder="ws-xxxxxxxx",
                help="例如 ws-022uxw9j9omqsn，不是完整 URL",
            )
            base_url = build_qwen_base_url(workspace_id) if workspace_id.strip() else None
            if base_url:
                st.text_input("Base URL（自动生成）", value=base_url, disabled=True)
            model = st.text_input("模型", value=qwen_model or "qwen-plus", help="如 qwen-plus、qwen3.7-max、qwen-turbo")
        else:
            api_key = st.text_input(
                "API Key",
                value=openai_key,
                type="password",
                help="也可在 Streamlit Secrets 中配置 openai.api_key",
            )
            base_url = st.text_input(
                "Base URL（可选）",
                value=openai_base,
                placeholder="https://api.openai.com/v1",
                help="DeepSeek、Moonshot 等兼容 OpenAI 的地址",
            ) or None
            model = st.text_input("模型", value=openai_model or "gpt-4o-mini")

        enable_search = st.toggle("联网检索", value=True, help="涉及专业/就业等问题时先搜公开信息")
        st.divider()
        st.caption("Skill 来源")
        st.markdown("[XinaiLU/zhangxuefeng-skill](https://github.com/XinaiLU/zhangxuefeng-skill)")
        st.caption("仅供学习交流，角色扮演非本人观点。")
    return api_key, base_url or None, model, enable_search


def main() -> None:
    init_state()
    api_key, base_url, model, enable_search = render_sidebar()

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
    st.caption("高考志愿 / 考研 / 职业规划 — 基于 zhangxuefeng-skill 的 Streamlit 对话前端")

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

    if not api_key:
        st.error("请先在左侧侧边栏填写 API Key。")
        return

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    search_context = None
    if enable_search and needs_web_search(prompt):
        with st.status("张雪峰正在查数据…", expanded=False):
            search_context = web_search(f"{prompt} 2026 就业 薪资 录取", max_results=5)

    system_prompt = build_system_prompt(search_context)
    client = create_client(api_key, base_url)
    history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[:-1]]

    with st.chat_message("assistant", avatar="🎓"):
        placeholder = st.empty()
        try:
            chunks: list[str] = []
            for piece in chat_stream(
                client,
                model=model,
                system_prompt=system_prompt,
                messages=[*history, {"role": "user", "content": prompt}],
            ):
                chunks.append(piece)
                placeholder.markdown("".join(chunks))
            reply = "".join(chunks)
        except Exception as exc:
            err = str(exc)
            st.error(f"模型调用失败: {err}")
            if "404" in err:
                st.info(
                    "常见原因：① Base URL 不完整（通义需填 Workspace ID，不是 `https://ws-xxx`）；"
                    "② 模型名拼写错误；③ Key 与地域不匹配。"
                    "通义正确格式：`https://ws-你的ID.cn-beijing.maas.aliyuncs.com/compatible-mode/v1`"
                )
            return

    st.session_state.messages.append({"role": "assistant", "content": reply})


if __name__ == "__main__":
    main()
