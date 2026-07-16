# Conversation Library v1.8 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add pinned local chat sessions and title-plus-message session search while preserving existing JSON compatibility.

**Architecture:** Extend the existing `ai_chat.sessions` domain module with a persisted `pinned` field, deterministic pin helpers, pinned-first sorting, and message-content search. Keep Streamlit changes in `app.py` limited to using those helpers from the Sessions sidebar, with README and changelog updates at the end.

**Tech Stack:** Python, Streamlit, pytest, Ruff, local JSON storage.

---

## File Structure

- Modify `ai_chat/sessions.py`: add the `pinned` model field, preserve it across mutations, parse it during load/import, export it to JSON, add `set_session_pinned`, add `sort_sessions`, and add `search_sessions`.
- Modify `tests/test_sessions.py`: add unit coverage for pinned compatibility, pinned export/import, pin helper behavior, pinned sorting, and message-content search.
- Modify `app.py`: switch sidebar code to `sort_sessions` and `search_sessions`, add the active-chat pin/unpin button, and preserve active-session behavior during search.
- Modify `README.md`: document pinned sessions, title/message search, and local JSON compatibility.
- Modify `CHANGELOG.md`: add v1.8 release notes.

Use this verification command shape in this workspace:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp .pytest_cache/tmp
.\.venv\Scripts\python.exe -m compileall app.py ai_chat
.\.venv\Scripts\python.exe -m ruff check .
```

The `--basetemp .pytest_cache/tmp` flag keeps pytest temporary files inside the repository on Windows.

## Task 1: Session Pinned Model Compatibility

**Files:**
- Modify: `ai_chat/sessions.py`
- Modify: `tests/test_sessions.py`

- [ ] **Step 1: Write failing pinned model tests**

In `tests/test_sessions.py`, update the import block to include `json` and `session_to_dict`:

```python
import json

from ai_chat.sessions import (
    ChatSession,
    create_default_session,
    create_session,
    delete_last_turn,
    delete_session,
    derive_session_title,
    export_session_json,
    export_sessions_json,
    filter_sessions_by_title,
    import_sessions_json,
    load_sessions,
    maybe_auto_title_session,
    rename_session,
    save_sessions,
    session_to_dict,
    sort_sessions_by_updated_at,
    update_session_messages,
)
```

After `test_create_default_session`, add:

```python
def test_create_default_session_is_unpinned():
    session = create_default_session()

    assert session.pinned is False
```

After `test_create_session_falls_back_for_empty_title`, add:

```python
def test_create_session_is_unpinned():
    session = create_session("Project notes")

    assert session.pinned is False
```

After `test_update_session_messages_preserves_metadata_and_updates_timestamp`, add:

```python
def test_session_mutations_preserve_pinned_state():
    session = ChatSession(
        id="session-1",
        title="Untitled chat",
        messages=[{"role": "user", "content": "Hello"}],
        created_at="2026-07-15T00:00:00Z",
        updated_at="2026-07-15T00:00:00Z",
        pinned=True,
    )

    titled = maybe_auto_title_session(session, "Explain local storage")
    renamed = rename_session(session, "Pinned notes")
    updated = update_session_messages(
        session,
        [{"role": "user", "content": "Updated"}],
    )
    trimmed = delete_last_turn(session)

    assert titled.pinned is True
    assert renamed.pinned is True
    assert updated.pinned is True
    assert trimmed.pinned is True
```

After `test_load_sessions_backs_up_corrupt_file`, add:

```python
def test_session_from_old_json_defaults_to_unpinned(tmp_path):
    path = tmp_path / "chats.json"
    payload = {
        "sessions": [
            {
                "id": "session-1",
                "title": "Old backup",
                "messages": [{"role": "user", "content": "Hello"}],
                "created_at": "2026-07-15T00:00:00Z",
                "updated_at": "2026-07-15T00:00:00Z",
            }
        ]
    }
    path.write_text(json.dumps(payload), encoding="utf-8")

    loaded = load_sessions(path)

    assert len(loaded) == 1
    assert loaded[0].pinned is False


def test_session_from_json_uses_false_for_invalid_pinned(tmp_path):
    path = tmp_path / "chats.json"
    payload = {
        "sessions": [
            {
                "id": "session-1",
                "title": "Invalid pinned",
                "messages": [{"role": "user", "content": "Hello"}],
                "created_at": "2026-07-15T00:00:00Z",
                "updated_at": "2026-07-15T00:00:00Z",
                "pinned": "yes",
            }
        ]
    }
    path.write_text(json.dumps(payload), encoding="utf-8")

    loaded = load_sessions(path)

    assert loaded[0].pinned is False
```

After `test_export_session_json_round_trips`, add:

```python
def test_session_json_includes_pinned_state():
    session = ChatSession(
        id="session-1",
        title="Pinned",
        messages=[],
        created_at="2026-07-15T00:00:00Z",
        updated_at="2026-07-15T00:00:00Z",
        pinned=True,
    )

    exported = json.loads(export_session_json(session))

    assert session_to_dict(session)["pinned"] is True
    assert exported["pinned"] is True


def test_import_session_json_preserves_pinned_state():
    session = ChatSession(
        id="session-1",
        title="Pinned",
        messages=[],
        created_at="2026-07-15T00:00:00Z",
        updated_at="2026-07-15T00:00:00Z",
        pinned=True,
    )

    imported = import_sessions_json(export_session_json(session), existing_ids=set())

    assert len(imported) == 1
    assert imported[0].pinned is True
```

After `test_export_sessions_json_round_trips_multiple_sessions`, add:

```python
def test_export_sessions_json_preserves_pinned_state():
    first = ChatSession(
        id="first",
        title="Pinned",
        messages=[],
        created_at="2026-07-15T00:00:00Z",
        updated_at="2026-07-15T00:00:00Z",
        pinned=True,
    )
    second = create_session("Regular")

    imported = import_sessions_json(export_sessions_json([first, second]), existing_ids=set())

    assert [session.pinned for session in imported] == [True, False]
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_sessions.py -q --basetemp .pytest_cache/tmp
```

Expected: FAIL because `ChatSession` has no `pinned` field and exports do not include `pinned`.

- [ ] **Step 3: Implement pinned model compatibility**

In `ai_chat/sessions.py`, update `ChatSession`:

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

Update `maybe_auto_title_session`:

```python
def maybe_auto_title_session(session: ChatSession, prompt: str) -> ChatSession:
    if session.title != DEFAULT_TITLE:
        return session
    return ChatSession(
        id=session.id,
        title=derive_session_title(prompt),
        messages=session.messages,
        created_at=session.created_at,
        updated_at=utc_now(),
        pinned=session.pinned,
    )
```

Update `rename_session`:

```python
def rename_session(session: ChatSession, title: str) -> ChatSession:
    return ChatSession(
        id=session.id,
        title=safe_title(title),
        messages=session.messages,
        created_at=session.created_at,
        updated_at=utc_now(),
        pinned=session.pinned,
    )
```

Update `update_session_messages`:

```python
def update_session_messages(
    session: ChatSession, messages: list[dict[str, str]]
) -> ChatSession:
    return ChatSession(
        id=session.id,
        title=session.title,
        messages=messages,
        created_at=session.created_at,
        updated_at=utc_now(),
        pinned=session.pinned,
    )
```

Update `session_to_dict`:

```python
def session_to_dict(session: ChatSession) -> dict[str, object]:
    return {
        "id": session.id,
        "title": session.title,
        "messages": session.messages,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
        "pinned": session.pinned,
    }
```

In `session_from_dict`, add pinned parsing before the return:

```python
    raw_pinned = data.get("pinned", False)
    pinned = raw_pinned if isinstance(raw_pinned, bool) else False
```

Then pass it into `ChatSession`:

```python
    return ChatSession(
        id=session_id,
        title=safe_title(str(data.get("title", ""))),
        messages=messages,
        created_at=str(data.get("created_at") or now),
        updated_at=str(data.get("updated_at") or now),
        pinned=pinned,
    )
```

- [ ] **Step 4: Run task tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_sessions.py -q --basetemp .pytest_cache/tmp
```

Expected: PASS for `tests/test_sessions.py`.

- [ ] **Step 5: Run lint and compile checks**

Run:

```powershell
.\.venv\Scripts\python.exe -m compileall app.py ai_chat
.\.venv\Scripts\python.exe -m ruff check .
```

Expected:

- compile command succeeds.
- Ruff reports `All checks passed!`.

- [ ] **Step 6: Commit Task 1**

Run:

```powershell
git status --short
git add ai_chat/sessions.py tests/test_sessions.py
git diff --cached --check
git commit -m "feat: add pinned session model field"
```

Expected: commit succeeds with only `ai_chat/sessions.py` and `tests/test_sessions.py` staged.

## Task 2: Pinned Sorting and Pin Helper

**Files:**
- Modify: `ai_chat/sessions.py`
- Modify: `tests/test_sessions.py`

- [ ] **Step 1: Write failing sorting and pin helper tests**

In the `tests/test_sessions.py` import block, add:

```python
    set_session_pinned,
    sort_sessions,
```

After `test_delete_session_selects_remaining_session`, add:

```python
def test_set_session_pinned_updates_state_and_timestamp():
    session = ChatSession(
        id="session-1",
        title="Chat",
        messages=[{"role": "user", "content": "Hello"}],
        created_at="2026-07-15T00:00:00Z",
        updated_at="2026-07-15T00:00:00Z",
        pinned=False,
    )

    updated = set_session_pinned(session, True)

    assert updated.id == "session-1"
    assert updated.title == "Chat"
    assert updated.messages == [{"role": "user", "content": "Hello"}]
    assert updated.created_at == "2026-07-15T00:00:00Z"
    assert updated.pinned is True
    assert updated.updated_at != "2026-07-15T00:00:00Z"
```

Replace `test_sort_sessions_by_updated_at_uses_newest_first` with:

```python
def test_sort_sessions_orders_pinned_first_then_newest():
    pinned_older = ChatSession(
        id="pinned-older",
        title="Pinned Older",
        messages=[],
        created_at="2026-07-15T00:00:00Z",
        updated_at="2026-07-15T01:00:00Z",
        pinned=True,
    )
    pinned_newer = ChatSession(
        id="pinned-newer",
        title="Pinned Newer",
        messages=[],
        created_at="2026-07-15T00:00:00Z",
        updated_at="2026-07-15T02:00:00Z",
        pinned=True,
    )
    regular_newer = ChatSession(
        id="regular-newer",
        title="Regular Newer",
        messages=[],
        created_at="2026-07-15T00:00:00Z",
        updated_at="2026-07-15T03:00:00Z",
        pinned=False,
    )
    regular_older = ChatSession(
        id="regular-older",
        title="Regular Older",
        messages=[],
        created_at="2026-07-15T00:00:00Z",
        updated_at="2026-07-15T00:30:00Z",
        pinned=False,
    )

    sorted_sessions = sort_sessions(
        [regular_newer, pinned_older, regular_older, pinned_newer]
    )

    assert sorted_sessions == [
        pinned_newer,
        pinned_older,
        regular_newer,
        regular_older,
    ]
```

After it, add:

```python
def test_sort_sessions_by_updated_at_wraps_sort_sessions():
    pinned = ChatSession(
        id="pinned",
        title="Pinned",
        messages=[],
        created_at="2026-07-15T00:00:00Z",
        updated_at="2026-07-15T01:00:00Z",
        pinned=True,
    )
    regular = ChatSession(
        id="regular",
        title="Regular",
        messages=[],
        created_at="2026-07-15T00:00:00Z",
        updated_at="2026-07-15T02:00:00Z",
        pinned=False,
    )

    assert sort_sessions_by_updated_at([regular, pinned]) == [pinned, regular]
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_sessions.py -q --basetemp .pytest_cache/tmp
```

Expected: FAIL because `set_session_pinned` and `sort_sessions` do not exist yet.

- [ ] **Step 3: Implement pin helper and sorting**

In `ai_chat/sessions.py`, after `delete_session`, add:

```python
def set_session_pinned(session: ChatSession, pinned: bool) -> ChatSession:
    return ChatSession(
        id=session.id,
        title=session.title,
        messages=session.messages,
        created_at=session.created_at,
        updated_at=utc_now(),
        pinned=pinned,
    )


def sort_sessions(sessions: list[ChatSession]) -> list[ChatSession]:
    return sorted(
        sessions,
        key=lambda session: (session.pinned, session.updated_at),
        reverse=True,
    )
```

Replace `sort_sessions_by_updated_at` with:

```python
def sort_sessions_by_updated_at(sessions: list[ChatSession]) -> list[ChatSession]:
    return sort_sessions(sessions)
```

- [ ] **Step 4: Run task tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_sessions.py -q --basetemp .pytest_cache/tmp
```

Expected: PASS for `tests/test_sessions.py`.

- [ ] **Step 5: Run lint and compile checks**

Run:

```powershell
.\.venv\Scripts\python.exe -m compileall app.py ai_chat
.\.venv\Scripts\python.exe -m ruff check .
```

Expected:

- compile command succeeds.
- Ruff reports `All checks passed!`.

- [ ] **Step 6: Commit Task 2**

Run:

```powershell
git status --short
git add ai_chat/sessions.py tests/test_sessions.py
git diff --cached --check
git commit -m "feat: support pinned chat session sorting"
```

Expected: commit succeeds with only `ai_chat/sessions.py` and `tests/test_sessions.py` staged.

## Task 3: Title and Message Session Search

**Files:**
- Modify: `ai_chat/sessions.py`
- Modify: `tests/test_sessions.py`

- [ ] **Step 1: Write failing session search tests**

In the `tests/test_sessions.py` import block, add:

```python
    search_sessions,
```

Replace `test_filter_sessions_by_title_matches_case_insensitive_substring` and `test_filter_sessions_by_title_returns_all_for_blank_query` with:

```python
def test_search_sessions_matches_title_case_insensitive_substring():
    first = ChatSession(
        id="first",
        title="Project Notes",
        messages=[],
        created_at="2026-07-15T00:00:00Z",
        updated_at="2026-07-15T00:00:00Z",
    )
    second = ChatSession(
        id="second",
        title="DeepSeek Debug",
        messages=[],
        created_at="2026-07-15T00:00:00Z",
        updated_at="2026-07-15T00:00:00Z",
    )

    assert search_sessions([first, second], "project") == [first]
    assert search_sessions([first, second], "DEBUG") == [second]


def test_search_sessions_matches_user_message_content():
    first = ChatSession(
        id="first",
        title="First",
        messages=[{"role": "user", "content": "Plan the release checklist"}],
        created_at="2026-07-15T00:00:00Z",
        updated_at="2026-07-15T00:00:00Z",
    )
    second = ChatSession(
        id="second",
        title="Second",
        messages=[{"role": "user", "content": "Debug provider settings"}],
        created_at="2026-07-15T00:00:00Z",
        updated_at="2026-07-15T00:00:00Z",
    )

    assert search_sessions([first, second], "release") == [first]


def test_search_sessions_matches_assistant_message_content():
    first = ChatSession(
        id="first",
        title="First",
        messages=[{"role": "assistant", "content": "Use Streamlit secrets."}],
        created_at="2026-07-15T00:00:00Z",
        updated_at="2026-07-15T00:00:00Z",
    )
    second = ChatSession(
        id="second",
        title="Second",
        messages=[{"role": "assistant", "content": "Write tests first."}],
        created_at="2026-07-15T00:00:00Z",
        updated_at="2026-07-15T00:00:00Z",
    )

    assert search_sessions([first, second], "secrets") == [first]


def test_search_sessions_returns_all_for_blank_query():
    first = create_session("First")
    second = create_session("Second")

    assert search_sessions([first, second], "   ") == [first, second]


def test_filter_sessions_by_title_keeps_title_only_behavior():
    first = ChatSession(
        id="first",
        title="Project Notes",
        messages=[{"role": "user", "content": "DeepSeek"}],
        created_at="2026-07-15T00:00:00Z",
        updated_at="2026-07-15T00:00:00Z",
    )
    second = ChatSession(
        id="second",
        title="DeepSeek Debug",
        messages=[],
        created_at="2026-07-15T00:00:00Z",
        updated_at="2026-07-15T00:00:00Z",
    )

    assert filter_sessions_by_title([first, second], "deepseek") == [second]
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_sessions.py -q --basetemp .pytest_cache/tmp
```

Expected: FAIL because `search_sessions` does not exist yet.

- [ ] **Step 3: Implement title and message search**

In `ai_chat/sessions.py`, after `sort_sessions_by_updated_at`, add:

```python
def search_sessions(sessions: list[ChatSession], query: str) -> list[ChatSession]:
    cleaned = query.strip().casefold()
    if not cleaned:
        return sessions

    return [
        session
        for session in sessions
        if cleaned in session.title.casefold()
        or any(
            cleaned in str(message.get("content", "")).casefold()
            for message in session.messages
            if isinstance(message, dict)
        )
    ]
```

Keep `filter_sessions_by_title` title-only:

```python
def filter_sessions_by_title(
    sessions: list[ChatSession], query: str
) -> list[ChatSession]:
    cleaned = query.strip().casefold()
    if not cleaned:
        return sessions
    return [session for session in sessions if cleaned in session.title.casefold()]
```

- [ ] **Step 4: Run task tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_sessions.py -q --basetemp .pytest_cache/tmp
```

Expected: PASS for `tests/test_sessions.py`.

- [ ] **Step 5: Run lint and compile checks**

Run:

```powershell
.\.venv\Scripts\python.exe -m compileall app.py ai_chat
.\.venv\Scripts\python.exe -m ruff check .
```

Expected:

- compile command succeeds.
- Ruff reports `All checks passed!`.

- [ ] **Step 6: Commit Task 3**

Run:

```powershell
git status --short
git add ai_chat/sessions.py tests/test_sessions.py
git diff --cached --check
git commit -m "feat: search chat sessions by message content"
```

Expected: commit succeeds with only `ai_chat/sessions.py` and `tests/test_sessions.py` staged.

## Task 4: Streamlit Sidebar Wiring

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Update session imports**

In `app.py`, replace this import list segment:

```python
from ai_chat.sessions import (
    ChatSession,
    create_session,
    delete_last_turn,
    delete_session,
    export_session_json,
    export_sessions_json,
    filter_sessions_by_title,
    import_sessions_json,
    load_sessions,
    maybe_auto_title_session,
    rename_session,
    save_sessions,
    sort_sessions_by_updated_at,
    update_session_messages,
)
```

with:

```python
from ai_chat.sessions import (
    ChatSession,
    create_session,
    delete_last_turn,
    delete_session,
    export_session_json,
    export_sessions_json,
    import_sessions_json,
    load_sessions,
    maybe_auto_title_session,
    rename_session,
    save_sessions,
    search_sessions,
    set_session_pinned,
    sort_sessions,
    update_session_messages,
)
```

- [ ] **Step 2: Replace sort helper use**

In `main()`, replace:

```python
        st.session_state.sessions = sort_sessions_by_updated_at(
            load_sessions(SESSION_STORE)
        )
```

with:

```python
        st.session_state.sessions = sort_sessions(load_sessions(SESSION_STORE))
```

In `replace_active_session()`, replace:

```python
    st.session_state.sessions = sort_sessions_by_updated_at(
        [
            updated if session.id == updated.id else session
            for session in st.session_state.sessions
        ]
    )
```

with:

```python
    st.session_state.sessions = sort_sessions(
        [
            updated if session.id == updated.id else session
            for session in st.session_state.sessions
        ]
    )
```

In the `New chat`, `Delete chat`, and successful import branches, replace each:

```python
        st.session_state.sessions = sort_sessions_by_updated_at(st.session_state.sessions)
```

with:

```python
        st.session_state.sessions = sort_sessions(st.session_state.sessions)
```

- [ ] **Step 3: Use title and message search in sidebar**

In `render_sessions_sidebar()`, replace:

```python
    visible_sessions = filter_sessions_by_title(st.session_state.sessions, query)
```

with:

```python
    visible_sessions = search_sessions(st.session_state.sessions, query)
```

- [ ] **Step 4: Add pin and unpin button**

In `render_sessions_sidebar()`, after:

```python
    if new_title != current.title:
        replace_active_session(rename_session(current, new_title))
```

add:

```python
    pin_label = "Unpin chat" if current.pinned else "Pin chat"
    if st.button(pin_label, use_container_width=True):
        replace_active_session(set_session_pinned(current, not current.pinned))
        st.rerun()
```

- [ ] **Step 5: Run full verification**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp .pytest_cache/tmp
.\.venv\Scripts\python.exe -m compileall app.py ai_chat
.\.venv\Scripts\python.exe -m ruff check .
```

Expected:

- pytest reports all tests passing.
- compile command succeeds.
- Ruff reports `All checks passed!`.

- [ ] **Step 6: Commit Task 4**

Run:

```powershell
git status --short
git add app.py
git diff --cached --check
git commit -m "feat: add pinned and full-text session controls"
```

Expected: commit succeeds with only `app.py` staged.

## Task 5: Documentation and Push

**Files:**
- Modify: `README.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Update README feature bullets**

In `README.md`, update the feature bullets from:

```markdown
- Recent-first session sorting and title search
```

to:

```markdown
- Pinned sessions, recent-first sorting, and title/message search
```

- [ ] **Step 2: Update README Local Sessions section**

In `README.md`, in the list under `The sidebar supports:`, replace:

```markdown
- Searching chats by title
```

with:

```markdown
- Searching chats by title and message content
- Pinning important chats above regular chats
```

Replace this paragraph:

```markdown
New chats are automatically titled from the first user prompt unless the chat already has a custom title. The session list is sorted by most recently updated chat first.
```

with:

```markdown
New chats are automatically titled from the first user prompt unless the chat already has a custom title. The session list shows pinned chats first, then sorts each group by most recently updated chat first. Pinned state is stored in `.data/chats.json`.
```

After that paragraph, add:

```markdown
The `Search chats` box searches chat titles and local message content. Older chat JSON files that do not include pinned state still load and import as unpinned chats.
```

- [ ] **Step 3: Update project structure if needed**

In `README.md`, update the `ai_chat/` tree if it does not list current modules. The expected block is:

```text
|-- ai_chat/
|   |-- chat.py              # Chat Completions helpers and export formatting
|   |-- config.py            # Provider configuration parsing
|   |-- preset_store.py      # Local custom prompt preset storage helpers
|   |-- presets.py           # Built-in prompt presets and prompt resolution
|   |-- runtime.py           # Runtime environment detection
|   `-- sessions.py          # Local chat session storage helpers
```

Keep surrounding README content unchanged.

- [ ] **Step 4: Add changelog entry**

At the top of `CHANGELOG.md`, after `# Changelog`, add:

```markdown
## v1.8 - Conversation Library

- Added pinned local chat sessions.
- Added title and message-content session search.
- Preserved pinned state in chat JSON import and export.
- Kept old chat JSON compatible by defaulting missing pinned state to unpinned.
```

- [ ] **Step 5: Run full verification**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp .pytest_cache/tmp
.\.venv\Scripts\python.exe -m compileall app.py ai_chat
.\.venv\Scripts\python.exe -m ruff check .
git diff --check
```

Expected:

- pytest reports all tests passing.
- compile command succeeds.
- Ruff reports `All checks passed!`.
- `git diff --check` prints no output.

- [ ] **Step 6: Commit Task 5 docs**

Run:

```powershell
git status --short
git add README.md CHANGELOG.md
git diff --cached --check
git commit -m "docs: document conversation library v1.8"
```

Expected: commit succeeds with only `README.md` and `CHANGELOG.md` staged.

- [ ] **Step 7: Push v1.8**

Run:

```powershell
git status --short --branch
git log --oneline origin/main..HEAD
git push
```

Expected:

- working tree is clean before push.
- recent commits include v1.8 design, v1.8 plan, pinned session model, pinned sorting, message search, Streamlit wiring, and docs.
- local `main` pushes to `origin/main`.
