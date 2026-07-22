# Session Management v1.10 Design

## Overview

v1.10 strengthens the local conversation library built across v1.8 and v1.9. The app already supports local multi-session storage, pinned sessions, title and message-content search, tags, notes, tag filtering, JSON import/export, and last-turn deletion. Those features make the chat library useful, but the current sidebar still has reliability and safety gaps when users start organizing more sessions.

This version focuses on safer session management and filtered-result operations. It stabilizes sidebar filter widget state across reruns, adds JSON export for the current filtered result set, adds batch tag operations for filtered sessions, and requires confirmation before deleting the active chat. The design stays local-first, deterministic, and JSON-backed. It does not introduce a database, account system, cloud sync, undo stack, or broader UI redesign.

## Goals

- Keep `Search chats` and `Filter tag` stable across Streamlit reruns triggered by session metadata edits and session actions.
- Let users export the currently visible filtered session list as JSON.
- Let users add one tag to all currently filtered sessions.
- Let users remove one tag from all currently filtered sessions.
- Prevent blank batch tag input from mutating sessions.
- Avoid duplicate tags when adding a tag that already exists with different casing.
- Remove tags case-insensitively.
- Require explicit confirmation before deleting the active chat.
- Preserve the current local JSON model under `.data/chats.json`.
- Preserve existing provider, streaming, prompt preset, custom preset, Markdown export, JSON import/export, pinned, search, tags, and notes behavior.

## Non-Goals

- No delete undo.
- No trash folder.
- No automatic `.data/` versioned backups.
- No bulk delete.
- No multi-select session picker.
- No multi-tag boolean query builder.
- No tag colors or tag management screen.
- No cloud sync, account system, or multi-device support.
- No database migration.
- No encryption for local `.data/` files.
- No Streamlit browser automation test suite.
- No main layout redesign.

## Recommended Approach

Keep `ai_chat.sessions` as the testable domain boundary for filter composition and batch tag mutation. Add a small helper that applies the existing title/message search and tag filter in one place, then use it from the Streamlit sidebar. Add batch tag helpers that accept the full session list, a set of selected session IDs, and one tag string; they should return a new session list while preserving unselected session objects.

Keep `app.py` responsible for Streamlit widget keys, download buttons, and action wiring. The sidebar should derive the current visible sessions once from the search query and tag filter, then reuse that list for the active-session selector, filtered export, and batch tag actions.

Alternative approaches considered:

- **Do everything in `app.py`:** This is fast, but it buries important filtering and batch mutation behavior inside Streamlit wiring and makes it hard to test.
- **Add a full selection UI:** More flexible, but it adds a larger interaction model than v1.10 needs. Filtered-result operations match the current sidebar workflow and keep scope small.
- **Add undo or backups now:** Useful later, but it needs broader data-safety design. v1.10 should first reduce the biggest immediate risk with delete confirmation.
- **Introduce a tag store:** This splits metadata away from sessions and complicates import/export. Tags should remain part of each `ChatSession`.

## User Experience

### Stable Filters

The Sessions sidebar should keep the text search and tag filter values stable after reruns. Reruns happen when users rename a chat, edit tags, edit a note, pin or unpin, import JSON, delete a session, or run batch tag operations. The controls should use explicit Streamlit session-state keys:

- `session_search_query`
- `session_tag_filter`

If the selected tag no longer exists after an operation, the app should reset the tag filter to `All tags` instead of crashing or keeping an invalid selectbox value.

The current hidden-active-session behavior should remain:

- If the active session is hidden by current filters, keep it active and show the hidden-session caption.
- If no sessions match, do not switch active sessions.

### Filtered JSON Export

The Sessions sidebar should add `Export Filtered JSON` near the existing JSON export controls. It should download the same JSON shape as `Export All JSON`, but only include sessions currently visible after search and tag filtering:

```json
{
  "sessions": []
}
```

When there are no matching sessions, the app should not produce a misleading empty backup as the primary action. A short caption is enough:

```text
Filtered JSON export is unavailable because no chats match.
```

The exported file should be importable through the existing JSON import control because it uses `export_sessions_json()`.

### Batch Tag Operations

The Sessions sidebar should add a small batch tag section for the current filtered result set:

- show how many chats match the current filters.
- accept one tag in a `Batch tag` text input.
- provide `Add tag to filtered chats`.
- provide `Remove tag from filtered chats`.

Both buttons should be disabled when there are no visible sessions or when the batch tag input normalizes to no tag. The operation should affect exactly the current visible sessions, not every local session.

Adding a tag should:

- trim the input.
- ignore blank input.
- avoid duplicates case-insensitively.
- preserve the first existing spelling/casing of duplicate tags.
- update `updated_at` only for sessions whose tag list actually changes.

Removing a tag should:

- trim the input.
- ignore blank input.
- match existing tags case-insensitively.
- update `updated_at` only for sessions whose tag list actually changes.

### Delete Confirmation

Deleting the active chat should require a checkbox:

```text
Confirm delete active chat
```

The `Delete chat` button should be disabled until the checkbox is selected. After deletion, the confirmation state should reset to false. Existing delete behavior should stay intact: deleting the last remaining session creates a new default chat automatically.

## Architecture

### `ai_chat.sessions`

Add or update helpers:

- `filter_visible_sessions(sessions: list[ChatSession], query: str, tag: str) -> list[ChatSession]`
- `replace_session_tags(session: ChatSession, tags: list[str]) -> ChatSession`
- `add_tag_to_sessions(sessions: list[ChatSession], session_ids: set[str], tag: str) -> list[ChatSession]`
- `remove_tag_from_sessions(sessions: list[ChatSession], session_ids: set[str], tag: str) -> list[ChatSession]`

`filter_visible_sessions` should compose existing helpers:

```python
filter_sessions_by_tag(search_sessions(sessions, query), tag)
```

`replace_session_tags` should be the common mutation primitive for batch tag operations. It should call `clean_tags()`, preserve all existing session fields, and return the original session unchanged if the cleaned tag list is equal to the current tag list.

`add_tag_to_sessions` and `remove_tag_from_sessions` should:

- return the original session list when the input tag is blank.
- return the original session list when `session_ids` is empty.
- mutate only sessions whose IDs are in `session_ids`.
- preserve unselected sessions exactly.
- preserve all metadata except tags and `updated_at` for changed sessions.

### `app.py`

Add explicit session-state defaults in `main()`:

- `session_search_query = ""`
- `session_tag_filter = "All tags"`
- `session_batch_tag = ""`
- `confirm_delete_active_chat = False`

Update `render_sessions_sidebar()`:

1. Render `Search chats` with `key="session_search_query"`.
2. Build tag options from `list_session_tags(st.session_state.sessions)`.
3. Reset `session_tag_filter` to `All tags` if the current value is unavailable.
4. Render `Filter tag` with `key="session_tag_filter"`.
5. Derive `visible_sessions` through `filter_visible_sessions()`.
6. Derive `visible_ids` once and reuse it for selectors and batch operations.
7. Render the existing active-session selector behavior.
8. Render `Batch tag`, `Add tag to filtered chats`, and `Remove tag from filtered chats`.
9. Render filtered JSON export.
10. Render delete confirmation before `Delete chat`.

The main chat flow should not change. Provider diagnostics, generation settings, streaming, prompt presets, custom preset loading, session import, Markdown export, and normal JSON exports should continue to use their current paths.

## Data Flow

1. App startup loads local sessions from `.data/chats.json`.
2. `main()` initializes explicit sidebar state keys.
3. Sidebar builds available tag options from all local sessions.
4. Sidebar normalizes an invalid selected tag back to `All tags`.
5. Sidebar computes visible sessions from search query and selected tag.
6. Active-session selector uses the visible session IDs without mutating sessions.
7. Filtered JSON export serializes `visible_sessions` through `export_sessions_json()`.
8. Batch tag operations mutate only `visible_ids`, save `.data/chats.json`, resort sessions, and rerun.
9. Delete confirmation gates `delete_session()`, resets confirmation state, saves `.data/chats.json`, and reruns.

## Error Handling

- Blank search returns all sessions that match the tag filter.
- `All tags` or blank tag filter returns all text-search matches.
- A selected tag that no longer exists resets to `All tags`.
- No filtered matches disables batch tag mutation and hides or replaces filtered export with a caption.
- Blank batch tag input disables both batch mutation buttons.
- Duplicate tag add returns unchanged sessions instead of bumping timestamps.
- Removing a missing tag returns unchanged sessions instead of bumping timestamps.
- Deleting without confirmation is not possible through the enabled button path.
- Deleting the final remaining chat still creates a default session.
- Corrupt `.data/chats.json` behavior remains unchanged: the file is moved aside and a default session is created.

## Testing

Unit tests should cover `ai_chat.sessions`:

- `filter_visible_sessions()` applies title/message search and tag filtering together.
- `filter_visible_sessions()` returns all sessions for blank filters.
- `add_tag_to_sessions()` updates selected sessions only.
- `add_tag_to_sessions()` ignores blank tags.
- `add_tag_to_sessions()` avoids case-insensitive duplicates.
- `remove_tag_from_sessions()` updates selected sessions only.
- `remove_tag_from_sessions()` removes tags case-insensitively.
- `remove_tag_from_sessions()` ignores blank or missing tags.
- Batch helpers preserve unselected sessions exactly.
- Batch helpers update `updated_at` only when a selected session actually changes.

Full verification:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp .pytest_cache/tmp
.\.venv\Scripts\python.exe -m compileall app.py ai_chat
.\.venv\Scripts\python.exe -m ruff check .
```

Documentation verification should also include:

```powershell
git diff --check
```

## Documentation

Update `README.md` with:

- filtered JSON export for matching chats.
- batch tag add/remove for filtered chats.
- delete confirmation for active chat deletion.
- note that filtered JSON exports use the same importable session JSON shape.
- note that deleting the last remaining chat still creates a new default chat.

Update `CHANGELOG.md` with a v1.10 entry.

## Success Criteria

- Search and tag filter values persist across Streamlit reruns.
- Invalid tag filter state recovers to `All tags`.
- Filtered JSON export contains exactly the currently visible sessions.
- Filtered JSON export can be imported through the existing import control.
- Batch tag add affects only visible sessions.
- Batch tag remove affects only visible sessions.
- Blank batch tag input cannot mutate sessions.
- Duplicate tag add and missing tag removal do not bump timestamps.
- Active chat deletion requires confirmation.
- Confirmation resets after deletion.
- Deleting the last remaining chat still leaves one default chat.
- Existing provider, streaming, prompt preset, custom preset, pinned, search, tags, notes, Markdown export, and JSON import/export behavior remains intact.
- All tests, compile checks, Ruff checks, and whitespace checks pass.
