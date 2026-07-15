from ai_chat.presets import (
    BUILT_IN_PRESETS,
    DEFAULT_PRESET_ID,
    get_preset,
    list_presets,
    resolve_system_prompt,
)


def test_built_in_presets_include_default():
    preset_ids = {preset.id for preset in BUILT_IN_PRESETS}

    assert DEFAULT_PRESET_ID == "general"
    assert DEFAULT_PRESET_ID in preset_ids


def test_list_presets_returns_built_in_presets():
    assert list_presets() == list(BUILT_IN_PRESETS)


def test_get_preset_returns_requested_preset():
    preset = get_preset("translator")

    assert preset.id == "translator"
    assert preset.name == "Translator"
    assert "translate" in preset.system_prompt.casefold()


def test_get_preset_falls_back_for_unknown_id():
    assert get_preset("missing") == get_preset(DEFAULT_PRESET_ID)


def test_resolve_system_prompt_prefers_non_empty_custom_prompt():
    assert resolve_system_prompt("general", "  Custom prompt  ") == "Custom prompt"


def test_resolve_system_prompt_falls_back_for_blank_custom_prompt():
    assert resolve_system_prompt("translator", "   ") == get_preset("translator").system_prompt
