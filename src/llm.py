from __future__ import annotations

from collections.abc import Iterator
from typing import Optional

from openai import OpenAI


def create_client(api_key: str, base_url: Optional[str]) -> OpenAI:
    kwargs: dict = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
    return OpenAI(**kwargs)


def chat_stream(
    client: OpenAI,
    *,
    model: str,
    system_prompt: str,
    messages: list[dict[str, str]],
    temperature: float = 0.8,
) -> Iterator[str]:
    stream = client.chat.completions.create(
        model=model,
        temperature=temperature,
        stream=True,
        messages=[{"role": "system", "content": system_prompt}, *messages],
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


def chat_once(
    client: OpenAI,
    *,
    model: str,
    system_prompt: str,
    messages: list[dict[str, str]],
    temperature: float = 0.3,
) -> str:
    response = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[{"role": "system", "content": system_prompt}, *messages],
    )
    return response.choices[0].message.content or ""
