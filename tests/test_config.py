import os

import pytest

from ai_chat.config import ProviderConfig, get_provider_diagnostic, load_provider_config


def test_loads_deepseek_config_by_default(monkeypatch):
    clear_ai_env(monkeypatch)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "deepseek-key")

    config = load_provider_config()

    assert config == ProviderConfig(
        provider="deepseek",
        api_key="deepseek-key",
        base_url="https://api.deepseek.com",
        model="deepseek-v4-pro",
    )


def test_loads_openai_config_when_selected(monkeypatch):
    clear_ai_env(monkeypatch)
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    monkeypatch.setenv("OPENAI_MODEL", "custom-openai-model")

    config = load_provider_config()

    assert config == ProviderConfig(
        provider="openai",
        api_key="openai-key",
        base_url="https://api.openai.com/v1",
        model="custom-openai-model",
    )


def test_rejects_unknown_provider(monkeypatch):
    clear_ai_env(monkeypatch)
    monkeypatch.setenv("AI_PROVIDER", "other")

    with pytest.raises(ValueError, match="Unsupported AI_PROVIDER"):
        load_provider_config()


def test_reports_missing_provider_api_key(monkeypatch):
    clear_ai_env(monkeypatch)
    monkeypatch.setenv("AI_PROVIDER", "deepseek")

    with pytest.raises(ValueError, match="DEEPSEEK_API_KEY"):
        load_provider_config()


def test_provider_diagnostic_reports_configured_key_without_leaking_secret(monkeypatch):
    clear_ai_env(monkeypatch)
    monkeypatch.setenv("AI_PROVIDER", "deepseek")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "super-secret-key")

    diagnostic = get_provider_diagnostic()

    assert diagnostic.provider == "deepseek"
    assert diagnostic.api_key_name == "DEEPSEEK_API_KEY"
    assert diagnostic.has_api_key is True
    assert "super-secret-key" not in diagnostic.status_text


def test_provider_diagnostic_reports_missing_key(monkeypatch):
    clear_ai_env(monkeypatch)
    monkeypatch.setenv("AI_PROVIDER", "openai")

    diagnostic = get_provider_diagnostic()

    assert diagnostic.provider == "openai"
    assert diagnostic.api_key_name == "OPENAI_API_KEY"
    assert diagnostic.has_api_key is False
    assert diagnostic.status_text == "OPENAI_API_KEY is not configured."


def clear_ai_env(monkeypatch):
    for key in list(os.environ):
        if key.startswith(("OPENAI_", "DEEPSEEK_")) or key == "AI_PROVIDER":
            monkeypatch.delenv(key, raising=False)
