# Conversation Library v1.8 Design

## Overview

v1.8 improves the local conversation library built across v1.4 and v1.5. The app already supports local multi-session storage, automatic titles, recent-first sorting, title search, JSON import/export, and last-turn deletion. Those features make short histories manageable, but longer local histories still become hard to navigate because important chats cannot be kept visible and search only checks titles.

This version adds pinned sessions and message-content search. The scope stays local-first and deterministic: no database, no embeddings, no cloud sync, and no AI calls for indexing or ranking. `ai_chat.sessions` remains the domain boundary for session model, sorting, searching, import/export compatibility, and testable helpers. `app.py` remains responsible for compact Streamlit wiring.

## Goals

- Let users pin important chats so they stay above regular chats.
- Let users unpin pinned chats without losing messages or metadata.
- Search sessions by title and message content from the existing sidebar search box.
- Keep search deterministic, case-insensitive, and substring-based.
- Preserve old `.data/chats.json` files by defaulting missing pinned metadata to `False`.
- Preserve existing provider, generation, streaming, prompt presets, custom presets, import/export, Markdown export, and deletion behavior.
- Keep all private chat and preset data in ignored local files under `.data/`.

## Non-Goals

- No semantic search, embeddings, vector database, or ranking model.
- No cloud account or remote sync.
- No tag system or folders.
- No per-message search highlighting.
- No search result snippets in v1.8.
- No migration script outside the normal load/save path.
- No redesign of the main chat layout.

## Recommended Approach

Extend `ChatSession` with a `pinned` boolean and update all session constructors and mutation helpers to preserve it. Update sorting so pinned sessions appear first, with `updated_at` descending inside pinned and unpinned groups. Replace the current title-only filter helper with a broader local search helper that checks the title and each message's content.

Alternative approaches considered:

- **Separate pinned ID list:** This avoids changing `ChatSession`, but splits one session concept across two persistence shapes and complicates import/export.
- **Tags instead of pinning:** Tags are useful, but they require more UI and filtering rules. Pinning addresses the most immediate "keep this visible" workflow with less scope.
- **Full search index:** An index could help very large histories, but local JSON and substring scan are simpler and sufficient for the expected app size.
- **Semantic search:** More powerful, but it needs provider coupling, embeddings, storage design, and privacy decisions that are larger than this release.

## Session Model

Add a new persisted field:

```python
@dataclass(frozen=True)
class ChatSession:
    id: str
    title: str
    messages: list[dict[str, str]]
    created_at: str
    updated_at: str
    pinned: bool = False
```

The default value keeps direct construction concise and makes old JSON compatible. Session load/import should parse `pinned` defensively:

- missing `pinned` -> `False`.
- boolean `pinned` -> keep value.
- non-boolean `pinned` -> `False`.

Session export should include `pinned` so backups preserve pinned state. Single-session JSON and all-session JSON both use the same `session_to_dict` path, so they should both carry the field after this change.

## User Experience

### Pin and Unpin

The Sessions sidebar should add one compact button for the active chat:

- `Pin chat` when the active chat is not pinned.
- `Unpin chat` when the active chat is pinned.

Clicking the button updates only the active session's `pinned` value and `updated_at`, saves `.data/chats.json`, resorts the session list, and reruns the app. Pinned sessions stay above unpinned sessions even when an unpinned session is more recently updated.

Built-in session actions keep their current behavior:

- `New chat` creates an unpinned session.
- `Delete chat` deletes pinned and unpinned sessions using the same rules.
- `Rename chat`, `Clear chat`, and `Delete last turn` preserve pinned state.
- Imported sessions keep their pinned state when present and default to unpinned when missing.

### Search

The existing `Search chats` input should search across:

- session title.
- every user message content.
- every assistant message content.

Search remains case-insensitive substring matching. Empty or whitespace-only search returns all sessions. Results retain the same global order produced by the session sorter, so pinned matches still appear before unpinned matches.

When the active session is hidden by the query, the current v1.5 behavior should remain: keep the active session stable and show `Active chat is hidden by the current search.` When no sessions match, keep the active session unchanged and show `No chats match the current search.`

The search box label can remain `Search chats`; README should clarify that it searches titles and message content.

## Architecture

### `ai_chat.sessions`

Update existing helpers and add focused helpers:

- `ChatSession(..., pinned: bool = False)`.
- `set_session_pinned(session: ChatSession, pinned: bool) -> ChatSession`.
- `sort_sessions(sessions: list[ChatSession]) -> list[ChatSession]`.
- `search_sessions(sessions: list[ChatSession], query: str) -> list[ChatSession]`.

`sort_sessions` should replace `sort_sessions_by_updated_at` as the preferred public helper. It sorts by pinned state first and `updated_at` second:

```python
return sorted(
    sessions,
    key=lambda session: (session.pinned, session.updated_at),
    reverse=True,
)
```

To keep the change low-risk, `sort_sessions_by_updated_at` can remain as a compatibility wrapper around `sort_sessions` for one release:

```python
def sort_sessions_by_updated_at(sessions: list[ChatSession]) -> list[ChatSession]:
    return sort_sessions(sessions)
```

`search_sessions` should replace `filter_sessions_by_title` as the preferred public helper. The older helper can remain as a compatibility wrapper if existing tests or plan steps still reference it.

Search implementation should inspect only message dictionaries with string-like values. It should not raise if a message is malformed after import cleanup.

### `app.py`

Update Streamlit wiring in the Sessions sidebar:

- Import and use `search_sessions` and `set_session_pinned`.
- Use `sort_sessions` after every session-list mutation.
- Render the active chat selector from `search_sessions(st.session_state.sessions, query)`.
- Add a `Pin chat` or `Unpin chat` button after the title input, before destructive actions.
- Preserve active-session stability when the query hides the active chat.

The main chat flow should not change. Prompt presets, custom preset loading, provider diagnostics, streaming, Markdown export, and JSON import/export should continue to work as before.

## Data Flow

1. App startup loads `.data/chats.json` through `load_sessions`.
2. `session_from_dict` defaults missing or invalid `pinned` values to `False`.
3. Loaded sessions are sorted with pinned sessions first, then newest updated first.
4. User types in `Search chats`; the sidebar filters the display list by title and message content.
5. User pins or unpins the active session; the app updates that session, saves the JSON file, resorts, and reruns.
6. User imports JSON; imported sessions keep valid pinned values and then join the sorted local list.
7. User exports JSON; exported sessions include `pinned`.

## Error Handling

- Old session JSON without `pinned` loads successfully as unpinned.
- Invalid `pinned` values are treated as `False`.
- Empty search returns all sessions.
- Search with no matches does not switch active sessions or crash the selectbox.
- Pinning or unpinning an active session preserves all messages, title, ID, and `created_at`.
- Deleting a pinned session follows existing delete behavior and never leaves the app with zero sessions.
- Corrupt `.data/chats.json` behavior remains unchanged: move the file aside and create a default session.

## Testing

Unit tests should cover `ai_chat.sessions`:

- `create_session` and `create_default_session` create unpinned sessions.
- `session_from_dict` defaults missing `pinned` to `False`.
- `session_from_dict` rejects non-boolean pinned values by using `False`.
- `session_to_dict`, `export_session_json`, and `export_sessions_json` include `pinned`.
- `import_sessions_json` preserves pinned state for single-session and multi-session JSON.
- `set_session_pinned` changes pinned state, preserves session content, and updates `updated_at`.
- `rename_session`, `update_session_messages`, `maybe_auto_title_session`, and `delete_last_turn` preserve pinned state.
- `sort_sessions` puts pinned sessions before unpinned sessions and sorts each group by newest `updated_at`.
- `search_sessions` matches titles case-insensitively.
- `search_sessions` matches user message content case-insensitively.
- `search_sessions` matches assistant message content case-insensitively.
- `search_sessions` returns all sessions for blank queries.
- `filter_sessions_by_title`, if kept, still filters only titles or delegates in a documented way.

Full verification should continue to use:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp .pytest_cache/tmp
.\.venv\Scripts\python.exe -m compileall app.py ai_chat
.\.venv\Scripts\python.exe -m ruff check .
```

The `--basetemp .pytest_cache/tmp` flag keeps pytest temporary files inside the workspace on Windows.

## Documentation

Update `README.md` with:

- pinned chat sessions.
- title and message-content search.
- note that pinned state is stored in `.data/chats.json`.
- note that old chat JSON without pinned state still imports as unpinned.

Update `CHANGELOG.md` with a v1.8 entry.

## Success Criteria

- Users can pin and unpin the active chat from the sidebar.
- Pinned sessions appear before regular sessions after startup and after every mutation.
- Session search matches title, user messages, and assistant messages.
- Old `.data/chats.json` files continue to load without manual migration.
- JSON import/export preserves pinned state.
- Existing session, prompt preset, custom preset, provider, streaming, and export behavior remains intact.
- All tests, compile checks, and Ruff checks pass.
