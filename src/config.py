from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import streamlit as st


@dataclass
class ApiConfig:
    api_key: str
    base_url: Optional[str]
    model: str
    enable_search: bool = True
    provider: str = "qwen"


def _secret(section: str, key: str, default: str = "") -> str:
    try:
        return str(st.secrets[section][key])
    except (KeyError, FileNotFoundError, AttributeError, TypeError):
        return default


def _secret_bool(section: str, key: str, default: bool = True) -> bool:
    raw = _secret(section, key, "")
    if raw == "":
        return default
    return raw.lower() in ("1", "true", "yes", "on")


def build_qwen_base_url(workspace_id: str) -> str:
    ws = workspace_id.strip().removeprefix("https://").split(".")[0]
    return f"https://{ws}.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"


def load_api_config() -> ApiConfig:
    """从 Streamlit Secrets 读取 API 配置，访客无需填写。"""
    enable_search = _secret_bool("app", "enable_search", default=True)

    qwen_key = _secret("qwen", "api_key")
    qwen_ws = _secret("qwen", "workspace_id")
    if qwen_key and qwen_ws:
        base_url = _secret("qwen", "base_url") or build_qwen_base_url(qwen_ws)
        return ApiConfig(
            api_key=qwen_key,
            base_url=base_url,
            model=_secret("qwen", "model", "qwen-plus"),
            enable_search=enable_search,
            provider="qwen",
        )

    openai_key = _secret("openai", "api_key")
    if openai_key:
        return ApiConfig(
            api_key=openai_key,
            base_url=_secret("openai", "base_url") or None,
            model=_secret("openai", "model", "gpt-4o-mini"),
            enable_search=enable_search,
            provider="openai",
        )

    return ApiConfig(api_key="", base_url=None, model="", enable_search=enable_search)
