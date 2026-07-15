# Conversation UX v1.5 Design

## Overview

v1.5 improves the local session experience added in v1.4. The app already supports multiple local sessions, JSON persistence, single-session JSON export, JSON import, and Markdown export. The next version should make those sessions easier to recognize, find, back up, and correct during normal use.

The scope stays intentionally small. This version does not add authentication, remote sync, database storage, full message editing, or a new frontend framework. It keeps Streamlit as the UI surface and `ai_chat.sessions` as the session domain boundary.

## Goals

- Automatically name new chats from the first user message.
- Show the most recently updated chats first.
- Let users search sessions by title.
- Export all sessions as one JSON backup file.
- Let users delete the last chat turn from the active session.
- Keep all private chat history in ignored local files under `.data/`.
- Preserve existing provider configuration, generation settings, streaming, Markdown export, and single-session JSON import/export.

## Non-Goals

- No database migration.
- No cloud account or remote session sync.
- No semantic search over message contents.
- No AI-generated titles that require an extra model call.
- No full message editing UI.
- No redesign of the main chat layout.

## Recommended Approach

Use deterministic local helpers in `ai_chat.sessions` and keep `app.py` responsible for Streamlit wiring. The domain helpers should handle title derivation, sorting, exporting all sessions, and deleting the last turn. This keeps behavior testable without launching Streamlit.

Alternative approaches were considered:

- **AI-generated titles:** Better titles, but adds latency, cost, provider coupling, and failure paths. Not worth it for this version.
- **Message-content search:** Useful later, but broader than a small UX polish release. Title search gives most of the benefit with much less complexity.
- **Browser storage or database storage:** More infrastructure than the app needs. The current local JSON store is enough for a simple AI chat project.

## User Experience

### Automatic Titles

When a user sends the first message in a chat whose title is still `Untitled chat`, the app should update the session title from the message text. The title is deterministic:

- Strip leading and trailing whitespace.
- Collapse internal whitespace to single spaces.
- Use at most 30 characters.
- Use `Untitled chat` when the prompt is empty after cleanup.

The app should not rename a chat once the user has manually renamed it or once it already has a non-default title.

### Session Sorting

The session selector should show sessions by `updated_at` descending, so the most recently active chat appears first. Sorting is only for display order and saved order; it must not change session IDs or message content.

After sending a message, renaming a session, clearing a chat, importing sessions, or deleting the last turn, the affected session's `updated_at` should move it to the top.

### Session Search

The sidebar should include a simple text input for filtering sessions by title. Search should be case-insensitive and match substrings.

If the active session is hidden by the current search query, the app should keep the active session stable internally and show an explanatory caption such as `Active chat is hidden by the current search.` The app should not silently switch sessions just because a filter is active.

If no sessions match the query, the selector should not render with an empty option list. It should show a small message and keep the active session unchanged.

### Export All JSON

The Sessions section should include an `Export All JSON` download button. It exports the same multi-session shape already accepted by `import_sessions_json`:

```json
{
  "sessions": []
}
```

The export should include every local session, not only the filtered sessions visible in search. File name: `simple-ai-chat-sessions.json`.

Single-session `Export JSON` stays available for sharing or backing up one chat.

### Delete Last Turn

The sidebar should include `Delete last turn` for the active session. A turn is the final user message plus its following assistant message when both exist. If the final message is an unmatched user or assistant message, delete only that final message.

The button should be disabled or omitted when the active session has no messages. After deletion, the active session should be saved and `updated_at` refreshed.

This gives users a practical way to remove an accidental prompt or failed assistant response without adding full message editing complexity.

## Architecture

### `ai_chat.sessions`

Add deterministic helpers:

- `derive_session_title(text: str, max_length: int = 30) -> str`
- `maybe_auto_title_session(session: ChatSession, prompt: str) -> ChatSession`
- `sort_sessions_by_updated_at(sessions: list[ChatSession]) -> list[ChatSession]`
- `filter_sessions_by_title(sessions: list[ChatSession], query: str) -> list[ChatSession]`
- `export_sessions_json(sessions: list[ChatSession]) -> str`
- `delete_last_turn(session: ChatSession) -> ChatSession`

These helpers should avoid Streamlit imports and file-system side effects, except existing persistence helpers such as `save_sessions`.

### `app.py`

Update Streamlit wiring:

- Apply `maybe_auto_title_session` when appending the first user prompt.
- Save sessions in sorted order after mutations.
- Add a search input above the active chat selector.
- Render the active chat selector from filtered sessions when matches exist.
- Add `Export All JSON`.
- Add `Delete last turn` for active sessions with messages.

The app should keep existing `Clear chat`, `Download Markdown`, single-session `Export JSON`, and `Import JSON` behavior.

## Data Flow

1. App startup loads `.data/chats.json` through `load_sessions`.
2. Sessions are sorted by `updated_at` before rendering the selector.
3. User types a search query; the sidebar filters the display list only.
4. User sends a prompt; the active session gets the user message, may receive an automatic title, and is saved.
5. Assistant response streams; the final assistant message is appended and saved.
6. User exports all sessions; `export_sessions_json` serializes the in-memory session list.
7. User deletes the last turn; `delete_last_turn` returns an updated session and the app saves the session list.

## Error Handling

- Empty or whitespace-only title derivation falls back to `Untitled chat`.
- Invalid imported JSON behavior remains unchanged: show `Invalid chat session JSON.`
- Search with no matches should not crash or switch sessions.
- Export all should still work when only one session exists.
- Delete last turn should be a no-op for empty sessions if called directly.

## Testing

Unit tests should cover the new pure helpers in `tests/test_sessions.py`:

- title derivation trims and collapses whitespace.
- title derivation truncates long prompts.
- automatic title only changes default-titled sessions.
- sorting puts latest `updated_at` first.
- filtering is case-insensitive and stable.
- exporting all sessions round-trips through `import_sessions_json`.
- deleting last turn removes user plus assistant when both exist.
- deleting last turn removes a single trailing unmatched message.
- deleting last turn is safe on empty sessions.

Full verification should continue to use:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp .pytest_cache/tmp
.\.venv\Scripts\python.exe -m compileall app.py ai_chat
.\.venv\Scripts\python.exe -m ruff check .
```

The `--basetemp .pytest_cache/tmp` flag avoids the Windows system temp permission issue already observed in this environment.

## Documentation

Update `README.md` to describe:

- automatic session titles.
- session search and recent-first sorting.
- exporting all sessions.
- deleting the last turn.

Update `CHANGELOG.md` with a v1.5 entry.

## Success Criteria

- New chats are automatically named from the first prompt.
- Recent sessions appear first.
- Users can filter sessions by title without losing the active session.
- Users can export every local session in one JSON file.
- Users can remove the last chat turn from the active session.
- Existing v1.4 local persistence, import, single-session export, and Markdown export continue to work.
- All tests, compile checks, and Ruff checks pass.
