from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from openai import OpenAI

from ai_chat.config import ProviderConfig

SYSTEM_PROMPT = "You are a concise, accurate AI assistant. Reply in Chinese by default."
ALLOWED_ROLES = {"user", "assistant", "system"}


@dataclass(frozen=True)
class GenerationSettings:
    temperature: float = 0.7
    max_tokens: int = 1024

    def __post_init__(self) -> None:
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError("temperature must be between 0.0 and 2.0.")
        if not 128 <= self.max_tokens <= 8192:
            raise ValueError("max_tokens must be between 128 and 8192.")


def build_chat_messages(
    history: Sequence[dict[str, str]], system_prompt: str | None = None
) -> list[dict[str, str]]:
    prompt = system_prompt.strip() if system_prompt else SYSTEM_PROMPT
    if not prompt:
        prompt = SYSTEM_PROMPT
    messages = [{"role": "system", "content": prompt}]
    for message in history:
        role = message.get("role", "")
        content = message.get("content", "")
        if role in ALLOWED_ROLES and content:
            messages.append({"role": role, "content": content})
    return messages


def create_chat_client(config: ProviderConfig) -> OpenAI:
    return OpenAI(api_key=config.api_key, base_url=config.base_url)


def request_chat_completion(
    client: OpenAI,
    config: ProviderConfig,
    history: Sequence[dict[str, str]],
    system_prompt: str | None = None,
) -> str:
    response = client.chat.completions.create(
        **build_chat_completion_kwargs(config, history, system_prompt=system_prompt)
    )
    message = response.choices[0].message.content
    return message or ""


def build_chat_completion_kwargs(
    config: ProviderConfig,
    history: Sequence[dict[str, str]],
    settings: GenerationSettings | None = None,
    *,
    stream: bool = False,
    system_prompt: str | None = None,
) -> dict[str, object]:
    kwargs: dict[str, object] = {
        "model": config.model,
        "messages": build_chat_messages(history, system_prompt),
    }
    if settings is not None:
        kwargs["temperature"] = settings.temperature
        kwargs["max_tokens"] = settings.max_tokens
    if stream:
        kwargs["stream"] = True
    if config.provider == "deepseek":
        kwargs["extra_body"] = {"thinking": {"type": "disabled"}}
    return kwargs


def stream_chat_completion(
    client: OpenAI,
    config: ProviderConfig,
    history: Sequence[dict[str, str]],
    settings: GenerationSettings,
    system_prompt: str | None = None,
) -> Iterable[str]:
    stream = client.chat.completions.create(
        **build_chat_completion_kwargs(
            config,
            history,
            settings,
            stream=True,
            system_prompt=system_prompt,
        )
    )
    for chunk in stream:
        delta = extract_stream_delta(chunk)
        if delta:
            yield delta


def extract_stream_delta(chunk: object) -> str:
    choices = getattr(chunk, "choices", [])
    if not choices:
        return ""
    delta = getattr(choices[0], "delta", None)
    if delta is None:
        return ""
    return getattr(delta, "content", None) or ""


def export_messages_to_markdown(
    messages: Sequence[dict[str, str]],
    *,
    provider: str,
    model: str,
) -> str:
    lines = [
        "# Simple AI Chat Export",
        "",
        f"- Provider: {provider}",
        f"- Model: {model}",
        "",
    ]
    for message in messages:
        role = message.get("role", "message").title()
        content = message.get("content", "")
        if not content:
            continue
        lines.extend([f"## {role}", "", content, ""])
    return "\n".join(lines).rstrip() + "\n"
