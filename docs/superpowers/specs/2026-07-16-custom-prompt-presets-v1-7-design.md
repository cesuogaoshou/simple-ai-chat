# Custom Prompt Presets v1.7 Design

## Overview

v1.7 extends the prompt preset workflow added in v1.6. The app currently ships built-in prompt presets and lets users enter a one-off custom system prompt in the sidebar. That custom prompt is useful for a single browser session, but repeated workflows still require copying the same instruction back into the text area.

This version adds local custom prompt presets. Users should be able to save a named prompt, select it again from the same preset selector, and delete it when it is no longer useful. The design stays local-first and keeps all chat session data unchanged.

## Goals

- Let users save the current custom system prompt as a reusable named preset.
- Load saved custom presets from local storage on app startup.
- Show built-in and custom presets in one prompt preset selector.
- Let users delete custom presets without affecting built-in presets.
- Keep custom preset logic testable outside Streamlit.
- Preserve existing provider, generation, session, import/export, Markdown export, and v1.6 prompt behavior.

## Non-Goals

- No cloud sync.
- No accounts or multi-user preset sharing.
- No prompt marketplace.
- No editing built-in presets.
- No advanced variable templating.
- No per-message preset history in chat exports.
- No change to `.data/chats.json` or the session import/export schema.

## Recommended Approach

Add a focused `ai_chat.preset_store` module for local custom preset persistence under `.data/presets.json`. Keep `ai_chat.presets` responsible for the preset catalog interface and prompt resolution, with built-in presets still defined in code. Update `app.py` to load custom presets, merge them into the selector, save the current custom prompt as a preset, and delete selected custom presets.

Alternative approaches considered:

- **Store custom presets in Streamlit session state only:** This is simple but loses presets when the browser session resets, which does not solve the repeated-workflow problem.
- **Store custom presets inside `.data/chats.json`:** This would reuse an existing file, but it mixes global prompt configuration with chat history and changes the meaning of session backup files.
- **Let users edit built-in presets in place:** This creates upgrade and reset ambiguity. Built-ins should stay deterministic; user changes should be separate custom presets.

## Preset Model

Built-in presets keep the current `PromptPreset` shape:

- stable `id`.
- display `name`.
- short `description`.
- `system_prompt`.

Custom presets should use the same shape at runtime so the UI and chat logic can treat all presets uniformly. Persisted custom presets should include:

- `id`: generated stable local ID, prefixed with `custom_`.
- `name`: user-entered display name.
- `description`: short generated or user-neutral description, such as `Custom prompt preset.`
- `system_prompt`: saved prompt text.
- `created_at`: UTC timestamp.
- `updated_at`: UTC timestamp.

Custom preset IDs must not collide with built-in IDs. If imported or loaded data has an invalid or duplicate ID, the store should generate a new custom ID rather than overwriting another preset.

## Local Storage

Use a new local JSON file:

```text
.data/presets.json
```

The `.data/` directory is already ignored by Git. The file should use this shape:

```json
{
  "presets": [
    {
      "id": "custom_...",
      "name": "My Reviewer",
      "description": "Custom prompt preset.",
      "system_prompt": "Review code for correctness and missing tests.",
      "created_at": "2026-07-16T00:00:00Z",
      "updated_at": "2026-07-16T00:00:00Z"
    }
  ]
}
```

Blank names should fall back to `Custom preset`. Blank prompts should not be saved. Corrupt JSON should be moved aside to `presets.invalid.json`, then the app should continue with no custom presets.

## User Experience

The existing sidebar `Prompt Preset` section should remain compact. It should support:

- selecting built-in and custom presets from one selectbox.
- seeing the selected preset description.
- entering a one-off custom system prompt as in v1.6.
- saving a non-empty custom system prompt as a named custom preset.
- deleting the selected custom preset.

Suggested sidebar controls:

- `Preset` selectbox.
- selected preset description caption.
- `Use custom system prompt` checkbox.
- `Custom system prompt` text area when enabled.
- `Custom preset name` text input when custom prompt is enabled.
- `Save as preset` button when custom prompt text is non-empty.
- `Delete custom preset` button only when the selected preset is custom.

Request behavior stays the same as v1.6:

- If custom system prompt is enabled and non-empty, use that custom prompt.
- Otherwise use the selected preset's system prompt.
- If custom prompt is enabled but blank, fall back to selected preset.

Saving a custom preset should not automatically write anything into chat history. Deleting a custom preset should move the active selection back to the default built-in preset if the deleted preset was selected.

## Architecture

### `ai_chat.preset_store`

Create a new module with pure local-storage helpers:

- `CUSTOM_PRESET_DESCRIPTION`.
- `CUSTOM_PRESET_ID_PREFIX`.
- `CustomPromptPreset` dataclass with `id`, `name`, `description`, `system_prompt`, `created_at`, and `updated_at`.
- `load_custom_presets(path: Path, reserved_ids: set[str]) -> list[CustomPromptPreset]`.
- `save_custom_presets(path: Path, presets: list[CustomPromptPreset]) -> None`.
- `create_custom_preset(name: str, system_prompt: str, existing_ids: set[str]) -> CustomPromptPreset | None`.
- `delete_custom_preset(presets: list[CustomPromptPreset], preset_id: str) -> list[CustomPromptPreset]`.
- `is_custom_preset_id(preset_id: str) -> bool`.
- `custom_to_prompt_preset(preset: CustomPromptPreset) -> PromptPreset`.

The module should avoid Streamlit imports and should be covered by unit tests. `CustomPromptPreset` is the persistence model. `PromptPreset` remains the runtime catalog model used by chat prompt resolution.

### `ai_chat.presets`

Keep built-in presets in code. Extend catalog helpers so callers can provide custom presets:

- `list_presets(custom_presets: Sequence[PromptPreset] = ()) -> list[PromptPreset]`.
- `get_preset(preset_id: str, custom_presets: Sequence[PromptPreset] = ()) -> PromptPreset`.
- `resolve_system_prompt(preset_id: str, custom_prompt: str = "", custom_presets: Sequence[PromptPreset] = ()) -> str`.

Built-ins should come first in the selector, followed by custom presets in saved creation order. Unknown IDs should continue to fall back to the default preset.

### `app.py`

Add a second local store constant:

```python
PRESET_STORE = Path(".data/presets.json")
```

Initialize Streamlit state for:

- `custom_presets`.
- `custom_preset_name`.

Load custom presets with `load_custom_presets(PRESET_STORE, reserved_ids={preset.id for preset in BUILT_IN_PRESETS})`. Convert them to runtime `PromptPreset` values before passing them into preset listing, lookup, and system prompt resolution.

When saving a preset:

1. Read `custom_preset_name` and `custom_system_prompt`.
2. Create a custom preset only if the prompt is non-empty.
3. Append it to `st.session_state.custom_presets`.
4. Save `.data/presets.json`.
5. Select the new preset and disable one-off custom prompt mode.
6. Rerun.

When deleting a custom preset:

1. Remove it from `st.session_state.custom_presets`.
2. Save `.data/presets.json`.
3. Set `preset_id` to `DEFAULT_PRESET_ID`.
4. Rerun.

## Data Flow

1. App starts and loads chat sessions from `.data/chats.json`.
2. App loads custom presets from `.data/presets.json`.
3. Sidebar renders built-in and custom presets in one selector.
4. User selects a preset or enters a one-off custom prompt.
5. User sends a message.
6. App resolves the active system prompt from custom text or selected preset.
7. Chat request includes the resolved system prompt.
8. Only user and assistant messages are saved to `.data/chats.json`.
9. Custom presets are saved only to `.data/presets.json`.

## Error Handling

- Blank custom prompt cannot be saved as a preset.
- Blank custom preset name falls back to `Custom preset`.
- Unknown selected preset ID falls back to the default built-in preset.
- Duplicate custom preset IDs are regenerated during load or create.
- Built-in preset IDs are reserved and cannot be overwritten by custom presets.
- Corrupt `.data/presets.json` is backed up to `presets.invalid.json`.
- Existing provider and chat request errors remain unchanged.

## Testing

Add unit tests for `ai_chat.preset_store`:

- loading missing file returns an empty list.
- saving and loading custom presets round trips.
- blank prompt is rejected when creating a custom preset.
- blank name falls back to `Custom preset`.
- reserved or duplicate IDs are regenerated on load.
- corrupt JSON is backed up and returns an empty list.
- deleting a custom preset removes only the requested ID.

Update `tests/test_presets.py`:

- `list_presets` includes custom presets after built-ins.
- `get_preset` can return a custom preset.
- `get_preset` falls back for unknown IDs when custom presets are present.
- `resolve_system_prompt` can resolve a selected custom preset.
- non-empty one-off custom prompt still overrides selected preset.

Full verification:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp .pytest_cache/tmp
.\.venv\Scripts\python.exe -m compileall app.py ai_chat
.\.venv\Scripts\python.exe -m ruff check .
```

## Documentation

Update `README.md` with:

- custom preset persistence under `.data/presets.json`.
- how to save and delete custom presets.
- note that custom presets are local and ignored by Git.

Update `CHANGELOG.md` with a v1.7 entry.

## Success Criteria

- Users can save a non-empty custom system prompt as a named preset.
- Saved custom presets survive app restarts.
- Built-in and custom presets appear in one selector.
- Users can delete custom presets but not built-in presets.
- Chat session JSON shape remains unchanged.
- Existing v1.6 prompt behavior still works.
- Tests, compile checks, and Ruff pass.
