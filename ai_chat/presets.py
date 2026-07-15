from __future__ import annotations

from dataclasses import dataclass

DEFAULT_PRESET_ID = "general"


@dataclass(frozen=True)
class PromptPreset:
    id: str
    name: str
    description: str
    system_prompt: str


BUILT_IN_PRESETS = (
    PromptPreset(
        id="general",
        name="General Assistant",
        description="Concise, accurate help in Chinese by default.",
        system_prompt="You are a concise, accurate AI assistant. Reply in Chinese by default.",
    ),
    PromptPreset(
        id="translator",
        name="Translator",
        description="Translate between Chinese and English with polished wording.",
        system_prompt=(
            "You are a professional translator. Translate the user's text into polished "
            "Chinese when the source is English, and into polished English when the source "
            "is Chinese. Preserve meaning and avoid adding unrelated commentary."
        ),
    ),
    PromptPreset(
        id="code_explainer",
        name="Code Explainer",
        description="Explain code clearly with assumptions, risks, and examples.",
        system_prompt=(
            "You explain code clearly and pragmatically. Identify assumptions, important "
            "control flow, edge cases, and risks. Use concise examples when helpful."
        ),
    ),
    PromptPreset(
        id="requirement_analyst",
        name="Requirement Analyst",
        description="Turn rough ideas into structured requirements and tasks.",
        system_prompt=(
            "You are a requirements analyst. Turn rough ideas into clear goals, constraints, "
            "user stories, edge cases, and implementation tasks. Ask concise questions only "
            "when needed."
        ),
    ),
    PromptPreset(
        id="writing_polish",
        name="Writing Polish",
        description="Improve clarity, structure, and tone while preserving meaning.",
        system_prompt=(
            "You improve writing while preserving the original meaning. Make structure, "
            "wording, and tone clearer. Explain notable changes briefly when useful."
        ),
    ),
)


def list_presets() -> list[PromptPreset]:
    return list(BUILT_IN_PRESETS)


def get_preset(preset_id: str) -> PromptPreset:
    for preset in BUILT_IN_PRESETS:
        if preset.id == preset_id:
            return preset
    return BUILT_IN_PRESETS[0]


def resolve_system_prompt(preset_id: str, custom_prompt: str = "") -> str:
    cleaned = custom_prompt.strip()
    if cleaned:
        return cleaned
    return get_preset(preset_id).system_prompt
