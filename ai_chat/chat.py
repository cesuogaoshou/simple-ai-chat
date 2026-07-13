from __future__ import annotations

from collections.abc import Sequence

from openai import OpenAI

from ai_chat.config import ProviderConfig


SYSTEM_PROMPT = "你是一个简洁、准确、默认使用中文回答的 AI 助手。"
ALLOWED_ROLES = {"user", "assistant", "system"}


def build_chat_messages(history: Sequence[dict[str, str]]) -> list[dict[str, str]]:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for message in history:
        role = message.get("role", "")
        content = message.get("content", "")
        if role in ALLOWED_ROLES and content:
            messages.append({"role": role, "content": content})
    return messages


def create_chat_client(config: ProviderConfig) -> OpenAI:
    return OpenAI(api_key=config.api_key, base_url=config.base_url)


def request_chat_completion(client: OpenAI, config: ProviderConfig, history: Sequence[dict[str, str]]) -> str:
    response = client.chat.completions.create(
        model=config.model,
        messages=build_chat_messages(history),
    )
    message = response.choices[0].message.content
    return message or ""
