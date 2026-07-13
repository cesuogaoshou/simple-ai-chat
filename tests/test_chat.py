from types import SimpleNamespace

import pytest

from ai_chat.chat import (
    SYSTEM_PROMPT,
    GenerationSettings,
    build_chat_messages,
    export_messages_to_markdown,
    extract_stream_delta,
    stream_chat_completion,
)
from ai_chat.config import ProviderConfig


def test_builds_chat_completion_messages_with_system_prompt():
    history = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi, how can I help?"},
    ]

    messages = build_chat_messages(history)

    assert messages == [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi, how can I help?"},
    ]


def test_ignores_messages_with_unknown_roles():
    history = [
        {"role": "tool", "content": "ignored"},
        {"role": "user", "content": "Keep this"},
    ]

    messages = build_chat_messages(history)

    assert messages == [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "Keep this"},
    ]


def test_generation_settings_defaults():
    settings = GenerationSettings()

    assert settings.temperature == 0.7
    assert settings.max_tokens == 1024


def test_extracts_delta_from_openai_compatible_stream_chunk():
    chunk = SimpleNamespace(
        choices=[
            SimpleNamespace(
                delta=SimpleNamespace(content="hello"),
            )
        ]
    )

    assert extract_stream_delta(chunk) == "hello"


def test_extract_stream_delta_returns_empty_string_for_missing_content():
    chunk = SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=None))])

    assert extract_stream_delta(chunk) == ""


def test_stream_chat_completion_passes_streaming_arguments():
    class FakeCompletions:
        def __init__(self):
            self.kwargs = None

        def create(self, **kwargs):
            self.kwargs = kwargs
            return [
                SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="Hi"))]),
                SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=" there"))]),
            ]

    fake_completions = FakeCompletions()
    fake_client = SimpleNamespace(chat=SimpleNamespace(completions=fake_completions))
    config = ProviderConfig(
        provider="deepseek",
        api_key="key",
        base_url="https://api.deepseek.com",
        model="deepseek-v4-pro",
    )

    chunks = list(
        stream_chat_completion(
            fake_client,
            config,
            [{"role": "user", "content": "Hello"}],
            GenerationSettings(temperature=0.2, max_tokens=256),
        )
    )

    assert chunks == ["Hi", " there"]
    assert fake_completions.kwargs["model"] == "deepseek-v4-pro"
    assert fake_completions.kwargs["stream"] is True
    assert fake_completions.kwargs["temperature"] == 0.2
    assert fake_completions.kwargs["max_tokens"] == 256


def test_exports_messages_to_markdown():
    markdown = export_messages_to_markdown(
        [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
        ],
        provider="deepseek",
        model="deepseek-v4-pro",
    )

    assert "# Simple AI Chat Export" in markdown
    assert "- Provider: deepseek" in markdown
    assert "- Model: deepseek-v4-pro" in markdown
    assert "## User" in markdown
    assert "Hello" in markdown
    assert "## Assistant" in markdown
    assert "Hi there" in markdown


def test_generation_settings_accepts_boundary_values():
    assert GenerationSettings(temperature=0.0, max_tokens=128).temperature == 0.0
    assert GenerationSettings(temperature=2.0, max_tokens=8192).max_tokens == 8192


def test_generation_settings_rejects_temperature_out_of_range():
    with pytest.raises(ValueError, match="temperature"):
        GenerationSettings(temperature=-0.1)

    with pytest.raises(ValueError, match="temperature"):
        GenerationSettings(temperature=2.1)


def test_generation_settings_rejects_max_tokens_out_of_range():
    with pytest.raises(ValueError, match="max_tokens"):
        GenerationSettings(max_tokens=127)

    with pytest.raises(ValueError, match="max_tokens"):
        GenerationSettings(max_tokens=8193)
