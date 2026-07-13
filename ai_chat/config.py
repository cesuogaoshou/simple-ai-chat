from __future__ import annotations

import os
from dataclasses import dataclass

SUPPORTED_PROVIDERS = {"deepseek", "openai"}


@dataclass(frozen=True)
class ProviderConfig:
    provider: str
    api_key: str
    base_url: str
    model: str


@dataclass(frozen=True)
class ProviderDiagnostic:
    provider: str
    api_key_name: str
    has_api_key: bool
    status_text: str


def get_provider_diagnostic() -> ProviderDiagnostic:
    provider = os.getenv("AI_PROVIDER", "deepseek").strip().lower()
    if provider not in SUPPORTED_PROVIDERS:
        return ProviderDiagnostic(
            provider=provider,
            api_key_name="",
            has_api_key=False,
            status_text=f"Unsupported AI_PROVIDER '{provider}'.",
        )

    api_key_name = f"{provider.upper()}_API_KEY"
    has_api_key = bool(os.getenv(api_key_name, "").strip())
    status = f"{api_key_name} is configured." if has_api_key else f"{api_key_name} is not configured."
    return ProviderDiagnostic(
        provider=provider,
        api_key_name=api_key_name,
        has_api_key=has_api_key,
        status_text=status,
    )


def load_provider_config() -> ProviderConfig:
    provider = os.getenv("AI_PROVIDER", "deepseek").strip().lower()
    if provider not in SUPPORTED_PROVIDERS:
        supported = ", ".join(sorted(SUPPORTED_PROVIDERS))
        raise ValueError(f"Unsupported AI_PROVIDER '{provider}'. Supported values: {supported}.")

    prefix = provider.upper()
    api_key_name = f"{prefix}_API_KEY"
    api_key = os.getenv(api_key_name, "").strip()
    if not api_key:
        raise ValueError(f"Missing {api_key_name}. Copy .env.example to .env and set a valid key.")

    return ProviderConfig(
        provider=provider,
        api_key=api_key,
        base_url=os.getenv(f"{prefix}_BASE_URL", default_base_url(provider)).strip(),
        model=os.getenv(f"{prefix}_MODEL", default_model(provider)).strip(),
    )


def default_base_url(provider: str) -> str:
    if provider == "openai":
        return "https://api.openai.com/v1"
    return "https://api.deepseek.com"


def default_model(provider: str) -> str:
    if provider == "openai":
        return "gpt-5.6"
    return "deepseek-v4-pro"
