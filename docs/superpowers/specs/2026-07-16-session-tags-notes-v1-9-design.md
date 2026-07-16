# Session Tags and Notes v1.9 Design

## Overview

v1.9 extends the local conversation library after v1.8. The app now supports local multi-session storage, automatic titles, pinned sessions, pinned-first sorting, title and message-content search, JSON import/export, and last-turn deletion. Those features make conversations easier to find, but users still need a lightweight way to classify chats and remember why a chat matters.

This version adds local session tags and notes. Tags provide simple categorization and filtering. Notes provide a short user-maintained description that is separate from chat messages. The design stays local-first, deterministic, and JSON-backed. It does not introduce a database, semantic search, AI-generated metadata, or a tag-management screen.

## Goals

- Let users attach multiple tags to each local chat session.
- Let users attach one free-text note to each local chat session.
- Let users filter visible sessions by one selected tag.
- Keep tags and notes in `.data/chats.json` with the rest of the session record.
- Preserve old chat JSON by defaulting missing `tags` to `[]` and missing `note` to `""`.
- Keep tag parsing, formatting, filtering, and metadata updates testable outside Streamlit.
- Preserve existing provider, generation, streaming, prompt presets, custom presets, pinned sessions, search, import/export, Markdown export, and deletion behavior.

## Non-Goals

- No tag colors.
- No tag management page.
- No folder hierarchy.
- No multi-tag boolean query builder.
- No AI-generated tags or summaries.
- No semantic search, embeddings, or vector database.
- No cloud sync or accounts.
- No separate database migration script.
- No redesign of the main chat layout.

## Recommended Approach

Extend `ChatSession` with two persisted fields: `tags: list[str]` and `note: str`. Keep `ai_chat.sessions` responsible for parsing, normalizing, formatting, updating, listing, and filtering tags. Keep `app.py` responsible for compact Streamlit controls in the existing Sessions sidebar.

Alternative approaches considered:

- **Separate tag store:** This avoids changing session JSON, but it splits session metadata away from the session it describes and complicates import/export.
- **Full tag management UI:** Useful later, but more UI than needed for a small local chat tool. A text input plus filter selectbox gives most of the value.
- **AI-generated tags and notes:** More automated, but adds latency, provider coupling, cost, and failure cases. v1.9 should stay deterministic.
- **Multiple tag filters at once:** More powerful, but Streamlit UI and edge cases grow quickly. One tag filter is enough for a first version.

## Session Model

Add two persisted fields:

```python
@dataclass(frozen=True)
class ChatSession:
    id: str
    title: str
    messages: list[dict[str, str]]
    created_at: str
    updated_at: str
    pinned: bool = False
    tags: list[str] | None = None
    note: str = ""
```

The runtime value should always behave like a list of strings. The plan can use `tags: list[str] = field(default_factory=list)` instead if the implementation updates the dataclass import. That is the preferred implementation because it avoids mutable default values.

Session load/import should parse tags defensively:

- missing `tags` -> `[]`.
- non-list `tags` -> `[]`.
- each tag is converted to text, stripped, and discarded if blank.
- duplicate tags are removed case-insensitively.
- the first spelling/casing seen is preserved.

Session load/import should parse notes defensively:

- missing `note` -> `""`.
- non-string `note` -> `str(value)`.
- note text is stored as-is except outer whitespace can be stripped when users update it through the UI.

Session export should include `tags` and `note`, so single-session and all-session JSON backups preserve the metadata.

## Tag Rules

Tags are simple text labels. Users enter them as comma-separated values:

```text
work, bug, research
```

Normalization rules:

- Split on commas.
- Strip leading and trailing whitespace.
- Drop blank entries.
- Deduplicate case-insensitively.
- Preserve the first user-entered spelling.
- Keep saved tag order stable.

Examples:

- `" work, bug, Work "` -> `["work", "bug"]`.
- `"research,, notes "` -> `["research", "notes"]`.
- `""` -> `[]`.

The UI should not enforce a fixed tag vocabulary. The available tag filter options come from existing session tags.

## User Experience

### Session Metadata Controls

In the Sessions sidebar, under the active chat title and pin/unpin controls, add:

- `Chat tags` text input with comma-separated tags.
- `Chat note` text area.

The controls should edit the active session only. Changes should save immediately when the widget value differs from the current session metadata. This matches existing title-edit behavior.

The current session selector behavior should remain stable:

- If the current search or tag filter hides the active session, keep the active session unchanged and show the existing hidden-session caption.
- If no sessions match the current filters, show the no-match caption and do not switch sessions.

### Tag Filter

Add a tag filter control near `Search chats`:

- Label: `Filter tag`.
- Options: `All tags` plus the sorted list of tags currently present in local sessions.

Filtering should be case-insensitive. Empty tag selection, represented by `All tags`, returns all sessions that match the text search. Filtering should preserve the existing session ordering; it should not re-sort or mutate sessions.

### Notes

Notes are session metadata, not chat messages. They should not be sent to the model and should not appear in Markdown conversation export. Notes should appear in JSON import/export because they are part of local session metadata.

## Architecture

### `ai_chat.sessions`

Add or update helpers:

- `normalize_session_tags(text: str) -> list[str]`.
- `format_session_tags(tags: list[str]) -> str`.
- `list_session_tags(sessions: list[ChatSession]) -> list[str]`.
- `filter_sessions_by_tag(sessions: list[ChatSession], tag: str) -> list[ChatSession]`.
- `update_session_tags(session: ChatSession, tags: list[str]) -> ChatSession`.
- `update_session_note(session: ChatSession, note: str) -> ChatSession`.

Existing mutation helpers should preserve `tags` and `note`:

- `maybe_auto_title_session`.
- `rename_session`.
- `update_session_messages`.
- `set_session_pinned`.
- `delete_last_turn` indirectly through `update_session_messages`.

Sorting remains unchanged from v1.8: pinned first, then `updated_at` descending.

Search remains unchanged from v1.8: title plus message content. It should not search notes in v1.9. Notes are metadata for the user, and including them in text search would make result behavior less explicit. Tag filtering is the metadata search path.

### `app.py`

Update the Sessions sidebar:

1. Read `query = st.text_input("Search chats", value="")`.
2. Build tag options with `list_session_tags(st.session_state.sessions)`.
3. Render `Filter tag` selectbox with `All tags` and current tags.
4. Build visible sessions by applying `search_sessions`, then `filter_sessions_by_tag`.
5. Render the existing active session selector behavior from the filtered list.
6. Render active chat title, pin/unpin, `Chat tags`, and `Chat note` controls.
7. Save metadata changes through `replace_active_session`.

The main chat flow should not change. Prompt presets, custom preset loading, provider diagnostics, streaming, Markdown export, and JSON import/export should continue to work as before.

## Data Flow

1. App startup loads `.data/chats.json` through `load_sessions`.
2. `session_from_dict` defaults missing or invalid tags and notes.
3. Sessions are sorted with pinned sessions first, then newest updated first.
4. Sidebar builds tag filter options from current local sessions.
5. Sidebar applies text search and selected tag filter to the display list.
6. User edits tags or note for the active session.
7. App updates the active session metadata, saves `.data/chats.json`, resorts, and reruns when needed.
8. JSON exports include tags and notes.
9. Markdown export remains message-only and does not include notes.

## Error Handling

- Old session JSON without tags or note loads successfully.
- Invalid `tags` values are treated as `[]`.
- Blank tag input clears tags.
- Duplicate tag input is deduplicated case-insensitively.
- Empty tag filter returns all text-search matches.
- Tag filter with no matches does not switch active sessions or crash the selectbox.
- Updating tags or note preserves messages, title, ID, `created_at`, and pinned state.
- Corrupt `.data/chats.json` behavior remains unchanged: move the file aside and create a default session.

## Testing

Unit tests should cover `ai_chat.sessions`:

- new sessions default to `tags=[]` and `note=""`.
- old JSON defaults missing metadata.
- invalid tags default to `[]`.
- duplicate tags are deduplicated case-insensitively.
- `session_to_dict`, single-session export, and all-session export include tags and note.
- import preserves tags and note.
- existing mutation helpers preserve tags and note.
- `normalize_session_tags` parses comma-separated text.
- `format_session_tags` joins tags for UI display.
- `update_session_tags` updates tags and timestamp.
- `update_session_note` updates note and timestamp.
- `list_session_tags` returns unique sorted tags.
- `filter_sessions_by_tag` matches case-insensitively.
- `filter_sessions_by_tag` returns all sessions for blank tag.

Full verification:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp .pytest_cache/tmp
.\.venv\Scripts\python.exe -m compileall app.py ai_chat
.\.venv\Scripts\python.exe -m ruff check .
```

## Documentation

Update `README.md` with:

- session tags and notes in the feature list.
- tag filtering in the Local Sessions section.
- note that tags and notes are stored in `.data/chats.json`.
- note that old chat JSON without tags or note still imports with empty metadata.

Update `CHANGELOG.md` with a v1.9 entry.

## Success Criteria

- Users can edit comma-separated tags for the active chat.
- Users can edit a note for the active chat.
- Users can filter visible sessions by one tag.
- Tags and notes survive app restarts.
- Old `.data/chats.json` files continue to load without manual migration.
- JSON import/export preserves tags and notes.
- Existing pinned session, search, prompt preset, custom preset, provider, streaming, and export behavior remains intact.
- All tests, compile checks, and Ruff checks pass.
