import json

from ai_chat.preset_store import (
    CUSTOM_PRESET_DESCRIPTION,
    CUSTOM_PRESET_ID_PREFIX,
    CustomPromptPreset,
    create_custom_preset,
    custom_to_prompt_preset,
    delete_custom_preset,
    is_custom_preset_id,
    load_custom_presets,
    save_custom_presets,
)


def test_load_custom_presets_returns_empty_for_missing_file(tmp_path):
    assert load_custom_presets(tmp_path / "presets.json", reserved_ids=set()) == []


def test_save_and_load_custom_presets_round_trips(tmp_path):
    path = tmp_path / "presets.json"
    preset = CustomPromptPreset(
        id="custom_reviewer",
        name="Reviewer",
        description=CUSTOM_PRESET_DESCRIPTION,
        system_prompt="Review the code.",
        created_at="2026-07-16T00:00:00Z",
        updated_at="2026-07-16T00:00:00Z",
    )

    save_custom_presets(path, [preset])
    loaded = load_custom_presets(path, reserved_ids=set())

    assert loaded == [preset]


def test_create_custom_preset_rejects_blank_prompt():
    assert create_custom_preset("Reviewer", "   ", existing_ids=set()) is None


def test_create_custom_preset_falls_back_for_blank_name():
    preset = create_custom_preset("   ", "Review code.", existing_ids=set())

    assert preset is not None
    assert preset.name == "Custom preset"
    assert preset.description == CUSTOM_PRESET_DESCRIPTION
    assert preset.system_prompt == "Review code."
    assert preset.id.startswith(CUSTOM_PRESET_ID_PREFIX)
    assert preset.created_at
    assert preset.updated_at == preset.created_at


def test_load_custom_presets_regenerates_reserved_and_duplicate_ids(tmp_path):
    path = tmp_path / "presets.json"
    payload = {
        "presets": [
            {
                "id": "general",
                "name": "Reserved",
                "description": "Custom prompt preset.",
                "system_prompt": "First prompt.",
                "created_at": "2026-07-16T00:00:00Z",
                "updated_at": "2026-07-16T00:00:00Z",
            },
            {
                "id": "custom_same",
                "name": "First",
                "description": "Custom prompt preset.",
                "system_prompt": "Second prompt.",
                "created_at": "2026-07-16T00:00:00Z",
                "updated_at": "2026-07-16T00:00:00Z",
            },
            {
                "id": "custom_same",
                "name": "Second",
                "description": "Custom prompt preset.",
                "system_prompt": "Third prompt.",
                "created_at": "2026-07-16T00:00:00Z",
                "updated_at": "2026-07-16T00:00:00Z",
            },
        ]
    }
    path.write_text(json.dumps(payload), encoding="utf-8")

    loaded = load_custom_presets(path, reserved_ids={"general"})
    loaded_ids = [preset.id for preset in loaded]

    assert len(loaded) == 3
    assert "general" not in loaded_ids
    assert len(set(loaded_ids)) == 3
    assert all(preset.id.startswith(CUSTOM_PRESET_ID_PREFIX) for preset in loaded)


def test_load_custom_presets_backs_up_corrupt_file(tmp_path):
    path = tmp_path / "presets.json"
    path.write_text("{not-json", encoding="utf-8")

    loaded = load_custom_presets(path, reserved_ids=set())

    assert loaded == []
    assert (tmp_path / "presets.invalid.json").exists()


def test_delete_custom_preset_removes_requested_id():
    first = CustomPromptPreset(
        id="custom_first",
        name="First",
        description=CUSTOM_PRESET_DESCRIPTION,
        system_prompt="First prompt.",
        created_at="2026-07-16T00:00:00Z",
        updated_at="2026-07-16T00:00:00Z",
    )
    second = CustomPromptPreset(
        id="custom_second",
        name="Second",
        description=CUSTOM_PRESET_DESCRIPTION,
        system_prompt="Second prompt.",
        created_at="2026-07-16T00:00:00Z",
        updated_at="2026-07-16T00:00:00Z",
    )

    assert delete_custom_preset([first, second], "custom_first") == [second]


def test_is_custom_preset_id_checks_prefix():
    assert is_custom_preset_id("custom_abc") is True
    assert is_custom_preset_id("general") is False


def test_custom_to_prompt_preset_drops_timestamps():
    custom = CustomPromptPreset(
        id="custom_reviewer",
        name="Reviewer",
        description=CUSTOM_PRESET_DESCRIPTION,
        system_prompt="Review the code.",
        created_at="2026-07-16T00:00:00Z",
        updated_at="2026-07-16T00:00:00Z",
    )

    runtime = custom_to_prompt_preset(custom)

    assert runtime.id == "custom_reviewer"
    assert runtime.name == "Reviewer"
    assert runtime.description == CUSTOM_PRESET_DESCRIPTION
    assert runtime.system_prompt == "Review the code."
