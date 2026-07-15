# Prompt Presets v1.6 Design

## Overview

v1.6 adds prompt presets to Simple AI Chat. The app currently supports provider configuration, streaming chat, local multi-session storage, session search, JSON import/export, Markdown export, and basic session cleanup. Prompt presets should make repeated workflows faster by letting users choose a reusable assistant mode such as general chat, translation, code review, explanation, or writing polish.

The design keeps the app simple. Presets are local configuration data, not remote resources. The first implementation should support built-in presets and a small custom system prompt field. It should not add accounts, a database, or a complex prompt marketplace.

## Goals

- Provide a small set of built-in prompt presets.
- Let the user select a preset in the sidebar before sending messages.
- Send the selected preset as the system message for future model requests.
- Let the user optionally override the selected preset with a custom system prompt.
- Keep preset logic testable outside Streamlit.
- Preserve current chat, session, export, generation, and provider behavior.

## Non-Goals

- No cloud preset sync.
- No multi-user preset management.
- No prompt marketplace.
- No per-message preset switching history in v1.6.
- No advanced variable templating such as `{language}` or `{tone}`.
- No storing custom presets as named reusable records yet.

## Recommended Approach

Add a focused `ai_chat.presets` module for preset definitions and selection helpers. Update `ai_chat.chat` so message construction accepts an optional system prompt. Update `app.py` sidebar controls to select a preset and optionally enter a custom system prompt. This keeps preset data separate from provider configuration and session persistence.

Alternative approaches were considered:

- **Hard-code presets directly in `app.py`:** Fast but mixes UI and domain behavior, making tests weaker and future preset work messier.
- **Persist presets in `.data/presets.json`:** Useful later, but not necessary for the first version. v1.6 should avoid another storage format until the preset workflow is proven.
- **Store preset metadata inside each chat session:** More historical detail, but it expands the session schema and import/export semantics. v1.6 should apply presets to outgoing requests without changing existing session JSON.

## Preset Catalog

Built-in presets should be deterministic and version-controlled:

- `General Assistant`: concise, accurate assistant; reply in Chinese by default.
- `Translator`: translate user input into polished Chinese or English depending on source language.
- `Code Explainer`: explain code clearly, call out assumptions, risks, and examples.
- `Requirement Analyst`: turn rough ideas into structured requirements and task breakdowns.
- `Writing Polish`: improve clarity, structure, and tone while preserving meaning.

Each preset has:

- stable `id`.
- display `name`.
- short `description`.
- `system_prompt`.

The default preset should match the current app behavior closely: concise, accurate, Chinese by default.

## User Experience

The sidebar gets a new `Prompt Preset` section near generation controls:

- Selectbox for built-in presets.
- Caption showing the selected preset description.
- Checkbox or toggle for `Use custom system prompt`.
- Text area for custom system prompt when enabled.

Request behavior:

- If custom system prompt is enabled and non-empty, use it.
- Otherwise use the selected preset's system prompt.
- If the custom prompt is enabled but blank, fall back to selected preset.

The UI should not display large instructional text explaining how presets work. Labels and concise captions are enough.

## Architecture

### `ai_chat.presets`

Create a new module with:

- `PromptPreset` dataclass.
- `DEFAULT_PRESET_ID`.
- `BUILT_IN_PRESETS`.
- `get_preset(preset_id: str) -> PromptPreset`.
- `list_presets() -> list[PromptPreset]`.
- `resolve_system_prompt(preset_id: str, custom_prompt: str = "") -> str`.

`get_preset` should return the default preset when an unknown ID is requested. `resolve_system_prompt` should trim custom text and prefer it only when non-empty.

### `ai_chat.chat`

Keep the existing default system prompt constant for compatibility, but route default prompt text through the new preset module or keep values aligned.

Update:

- `build_chat_messages(history, system_prompt=SYSTEM_PROMPT)`.
- `build_chat_completion_kwargs(..., system_prompt=None)`.
- `request_chat_completion(..., system_prompt=None)`.
- `stream_chat_completion(..., system_prompt=None)`.

When `system_prompt` is `None` or blank, use the existing default system prompt. This preserves existing tests and callers.

### `app.py`

Add sidebar state for:

- selected preset ID.
- custom system prompt enabled.
- custom system prompt text.

Pass the resolved system prompt into `stream_chat_completion`.

Do not persist preset selection into `.data/chats.json` in v1.6. Streamlit session state is enough for this version.

## Data Flow

1. App starts and initializes preset state with the default preset ID.
2. Sidebar renders preset selector and optional custom prompt field.
3. User sends a message.
4. App resolves the active system prompt from selected preset plus optional custom prompt.
5. `stream_chat_completion` builds Chat Completions messages with that system prompt.
6. Conversation messages are stored exactly as before; system prompt is not added to chat history.

## Error Handling

- Unknown preset ID falls back to the default preset.
- Blank custom prompt falls back to the selected preset.
- Whitespace-only custom prompt is treated as blank.
- Existing provider errors remain unchanged.
- Existing session import/export remains unchanged.

## Testing

Add unit tests for `ai_chat.presets`:

- built-in presets include the default ID.
- `get_preset` returns requested presets.
- `get_preset` falls back for unknown IDs.
- `resolve_system_prompt` uses custom non-empty text.
- `resolve_system_prompt` falls back for blank custom text.

Update `tests/test_chat.py`:

- `build_chat_messages` uses the default system prompt when none is provided.
- `build_chat_messages` uses a provided custom system prompt.
- `build_chat_completion_kwargs` passes the resolved system prompt into messages.
- streaming helper remains compatible with existing calls.

Full verification:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp .pytest_cache/tmp
.\.venv\Scripts\python.exe -m compileall app.py ai_chat
.\.venv\Scripts\python.exe -m ruff check .
```

## Documentation

Update `README.md` with:

- prompt preset feature summary.
- list of built-in presets.
- note that custom system prompts are local UI state in v1.6.

Update `CHANGELOG.md` with a v1.6 entry.

## Success Criteria

- Sidebar lets users choose a built-in prompt preset.
- Sidebar lets users optionally enter a custom system prompt.
- Chat requests use the resolved system prompt.
- Existing sessions and exports do not change shape.
- Existing v1.5 session behavior keeps working.
- Tests, compile checks, and Ruff pass.
