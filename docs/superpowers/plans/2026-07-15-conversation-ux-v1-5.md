# Conversation UX v1.5 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve local chat session usability with automatic titles, recent-first sorting, title search, all-session JSON export, and last-turn deletion.

**Architecture:** Keep `ai_chat.sessions` as the pure session domain boundary and keep `app.py` responsible for Streamlit UI wiring. Add deterministic, unit-tested helpers for title derivation, sorting, filtering, full export, and turn deletion, then connect those helpers to the sidebar and send-message flow.

**Tech Stack:** Python, Streamlit, pytest, Ruff, JSON persistence under `.data/`.

---

## File Structure

- Modify `ai_chat/sessions.py`: add pure session helpers for automatic titles, sorting, filtering, all-session export, and last-turn deletion.
- Modify `tests/test_sessions.py`: add unit tests for each new helper before implementation.
- Modify `app.py`: wire helpers into message send flow and sidebar controls.
- Modify `README.md`: document v1.5 user-facing session UX.
- Modify `CHANGELOG.md`: add v1.5 release notes.

Use `.\.venv\Scripts\python.exe -m pytest -q --basetemp .pytest_cache/tmp` for test runs in this workspace because the default Windows temp directory can raise permission errors.

## Task 1: Automatic Session Titles

**Files:**
- Modify: `ai_chat/sessions.py`
- Modify: `tests/test_sessions.py`

- [ ] **Step 1: Add failing title helper tests**

Update the import block in `tests/test_sessions.py`:

```python
from ai_chat.sessions import (
    ChatSession,
    create_default_session,
    create_session,
    delete_session,
    derive_session_title,
    export_session_json,
    import_sessions_json,
    load_sessions,
    maybe_auto_title_session,
    rename_session,
    save_sessions,
    update_session_messages,
)
```

Add these tests after `test_create_session_falls_back_for_empty_title`:

```python
def test_derive_session_title_cleans_whitespace():
    assert derive_session_title("  Build   a  small app  ") == "Build a small app"


def test_derive_session_title_truncates_long_prompt():
    title = derive_session_title("1234567890 1234567890 1234567890 extra")

    assert title == "1234567890 1234567890 123456"
    assert len(title) == 30


def test_derive_session_title_falls_back_for_blank_text():
    assert derive_session_title("   ") == "Untitled chat"


def test_maybe_auto_title_session_updates_default_title():
    session = ChatSession(
        id="session-1",
        title="Untitled chat",
        messages=[],
        created_at="2026-07-15T00:00:00Z",
        updated_at="2026-07-15T00:00:00Z",
    )

    updated = maybe_auto_title_session(session, "Explain local storage")

    assert updated.id == "session-1"
    assert updated.title == "Explain local storage"
    assert updated.messages == []
    assert updated.created_at == "2026-07-15T00:00:00Z"
    assert updated.updated_at != "2026-07-15T00:00:00Z"


def test_maybe_auto_title_session_preserves_custom_title():
    session = ChatSession(
        id="session-1",
        title="Project notes",
        messages=[],
        created_at="2026-07-15T00:00:00Z",
        updated_at="2026-07-15T00:00:00Z",
    )

    updated = maybe_auto_title_session(session, "A different prompt")

    assert updated == session
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_sessions.py -q --basetemp .pytest_cache/tmp
```

Expected: FAIL during collection with an import error for `derive_session_title` or `maybe_auto_title_session`.

- [ ] **Step 3: Implement title helpers**

In `ai_chat/sessions.py`, add `import re` near the existing imports:

```python
import json
import re
from dataclasses import dataclass
```

Add these helpers after `safe_title`:

```python
def derive_session_title(text: str, max_length: int = 30) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned:
        return DEFAULT_TITLE
    return cleaned[:max_length]


def maybe_auto_title_session(session: ChatSession, prompt: str) -> ChatSession:
    if session.title != DEFAULT_TITLE:
        return session
    return ChatSession(
        id=session.id,
        title=derive_session_title(prompt),
        messages=session.messages,
        created_at=session.created_at,
        updated_at=utc_now(),
    )
```

- [ ] **Step 4: Verify title tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_sessions.py -q --basetemp .pytest_cache/tmp
.\.venv\Scripts\python.exe -m ruff check .
```

Expected:

- `tests/test_sessions.py`: all tests pass.
- Ruff exits 0.

- [ ] **Step 5: Commit Task 1**

Run:

```powershell
git add ai_chat/sessions.py tests/test_sessions.py
git commit -m "feat: add automatic session titles"
```

## Task 2: Session Sorting and Title Filtering

**Files:**
- Modify: `ai_chat/sessions.py`
- Modify: `tests/test_sessions.py`

- [ ] **Step 1: Add failing sorting and filtering tests**

Update the import block in `tests/test_sessions.py`:

```python
from ai_chat.sessions import (
    ChatSession,
    create_default_session,
    create_session,
    delete_session,
    derive_session_title,
    export_session_json,
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

Add these tests after `test_delete_session_selects_remaining_session`:

```python
def test_sort_sessions_by_updated_at_uses_newest_first():
    older = ChatSession(
        id="older",
        title="Older",
        messages=[],
        created_at="2026-07-15T00:00:00Z",
        updated_at="2026-07-15T01:00:00Z",
    )
    newer = ChatSession(
        id="newer",
        title="Newer",
        messages=[],
        created_at="2026-07-15T00:00:00Z",
        updated_at="2026-07-15T02:00:00Z",
    )

    assert sort_sessions_by_updated_at([older, newer]) == [newer, older]


def test_filter_sessions_by_title_matches_case_insensitive_substring():
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

    assert filter_sessions_by_title([first, second], "project") == [first]
    assert filter_sessions_by_title([first, second], "DEBUG") == [second]


def test_filter_sessions_by_title_returns_all_for_blank_query():
    first = create_session("First")
    second = create_session("Second")

    assert filter_sessions_by_title([first, second], "   ") == [first, second]
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_sessions.py -q --basetemp .pytest_cache/tmp
```

Expected: FAIL during collection with an import error for `filter_sessions_by_title` or `sort_sessions_by_updated_at`.

- [ ] **Step 3: Implement sorting and filtering helpers**

Add these helpers in `ai_chat/sessions.py` after `delete_session`:

```python
def sort_sessions_by_updated_at(sessions: list[ChatSession]) -> list[ChatSession]:
    return sorted(sessions, key=lambda session: session.updated_at, reverse=True)


def filter_sessions_by_title(
    sessions: list[ChatSession], query: str
) -> list[ChatSession]:
    cleaned = query.strip().casefold()
    if not cleaned:
        return sessions
    return [session for session in sessions if cleaned in session.title.casefold()]
```

- [ ] **Step 4: Verify sorting and filtering tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_sessions.py -q --basetemp .pytest_cache/tmp
.\.venv\Scripts\python.exe -m ruff check .
```

Expected:

- `tests/test_sessions.py`: all tests pass.
- Ruff exits 0.

- [ ] **Step 5: Commit Task 2**

Run:

```powershell
git add ai_chat/sessions.py tests/test_sessions.py
git commit -m "feat: add session search and sorting helpers"
```

## Task 3: Wire Automatic Titles, Sorting, and Search into Streamlit

**Files:**
- Modify: `app.py`
- Modify: `ai_chat/sessions.py`
- Test: existing `tests/test_sessions.py`

- [ ] **Step 1: Update imports in `app.py`**

Change the `ai_chat.sessions` import block to include the new helpers:

```python
from ai_chat.sessions import (
    ChatSession,
    create_session,
    delete_session,
    export_session_json,
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

- [ ] **Step 2: Save sessions in recent-first order**

Replace `replace_active_session` in `app.py` with:

```python
def replace_active_session(updated: ChatSession) -> None:
    st.session_state.sessions = sort_sessions_by_updated_at(
        [
            updated if session.id == updated.id else session
            for session in st.session_state.sessions
        ]
    )
    save_sessions(SESSION_STORE, st.session_state.sessions)
```

- [ ] **Step 3: Sort sessions when loading and mutating lists**

In `main()`, replace the session initialization block with:

```python
    if "sessions" not in st.session_state:
        st.session_state.sessions = sort_sessions_by_updated_at(
            load_sessions(SESSION_STORE)
        )
        st.session_state.active_session_id = st.session_state.sessions[0].id
```

In the `New chat` button handler, replace the save line with:

```python
        st.session_state.sessions = sort_sessions_by_updated_at(st.session_state.sessions)
        save_sessions(SESSION_STORE, st.session_state.sessions)
```

In the `Delete chat` button handler, replace the save line with:

```python
        st.session_state.sessions = sort_sessions_by_updated_at(st.session_state.sessions)
        save_sessions(SESSION_STORE, st.session_state.sessions)
```

In the JSON import success branch, replace the save line with:

```python
            st.session_state.sessions = sort_sessions_by_updated_at(st.session_state.sessions)
            save_sessions(SESSION_STORE, st.session_state.sessions)
```

- [ ] **Step 4: Apply automatic title on first user prompt**

In `main()`, replace:

```python
    session = update_session_messages(session, messages)
    replace_active_session(session)
```

with:

```python
    session = maybe_auto_title_session(update_session_messages(session, messages), prompt)
    replace_active_session(session)
```

- [ ] **Step 5: Add session search to the sidebar**

In `render_sessions_sidebar()`, replace the initial selector block:

```python
    current = active_session()
    session_ids = [session.id for session in st.session_state.sessions]
    selected_id = st.selectbox(
        "Active chat",
        options=session_ids,
        index=session_ids.index(current.id),
        format_func=session_title_for_id,
    )
    st.session_state.active_session_id = selected_id
```

with:

```python
    current = active_session()
    query = st.text_input("Search chats", value="")
    visible_sessions = filter_sessions_by_title(st.session_state.sessions, query)
    visible_ids = [session.id for session in visible_sessions]
    if current.id in visible_ids:
        selected_id = st.selectbox(
            "Active chat",
            options=visible_ids,
            index=visible_ids.index(current.id),
            format_func=session_title_for_id,
        )
        st.session_state.active_session_id = selected_id
    elif visible_ids:
        st.caption("Active chat is hidden by the current search.")
        selected_id = st.selectbox(
            "Matching chats",
            options=visible_ids,
            index=None,
            format_func=session_title_for_id,
        )
        if selected_id is not None:
            st.session_state.active_session_id = selected_id
    else:
        st.caption("No chats match the current search.")
```

This keeps the active session stable when no sessions match, and it gives the user visible feedback if the active chat is hidden by the filter.

- [ ] **Step 6: Run verification**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp .pytest_cache/tmp
.\.venv\Scripts\python.exe -m compileall app.py ai_chat
.\.venv\Scripts\python.exe -m ruff check .
```

Expected:

- pytest exits 0.
- compileall exits 0.
- Ruff exits 0.

- [ ] **Step 7: Commit Task 3**

Run:

```powershell
git add app.py ai_chat/sessions.py tests/test_sessions.py
git commit -m "feat: add session search and automatic titles"
```

## Task 4: All Sessions Export and Last-Turn Deletion

**Files:**
- Modify: `ai_chat/sessions.py`
- Modify: `tests/test_sessions.py`

- [ ] **Step 1: Add failing export and delete-turn tests**

Update the import block in `tests/test_sessions.py`:

```python
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
    sort_sessions_by_updated_at,
    update_session_messages,
)
```

Add these tests near the existing JSON export tests:

```python
def test_export_sessions_json_round_trips_multiple_sessions():
    first = create_session("First")
    first.messages.append({"role": "user", "content": "Hello"})
    second = create_session("Second")
    second.messages.append({"role": "assistant", "content": "Hi"})

    exported = export_sessions_json([first, second])
    imported = import_sessions_json(exported, existing_ids=set())

    assert len(imported) == 2
    assert [session.title for session in imported] == ["First", "Second"]
    assert imported[0].messages == [{"role": "user", "content": "Hello"}]
    assert imported[1].messages == [{"role": "assistant", "content": "Hi"}]
```

Add these tests after `test_update_session_messages_preserves_metadata_and_updates_timestamp`:

```python
def test_delete_last_turn_removes_user_and_assistant_pair():
    session = ChatSession(
        id="session-1",
        title="Chat",
        messages=[
            {"role": "user", "content": "First"},
            {"role": "assistant", "content": "Reply"},
            {"role": "user", "content": "Remove me"},
            {"role": "assistant", "content": "Remove me too"},
        ],
        created_at="2026-07-15T00:00:00Z",
        updated_at="2026-07-15T00:00:00Z",
    )

    updated = delete_last_turn(session)

    assert updated.messages == [
        {"role": "user", "content": "First"},
        {"role": "assistant", "content": "Reply"},
    ]
    assert updated.updated_at != "2026-07-15T00:00:00Z"


def test_delete_last_turn_removes_single_trailing_message():
    session = ChatSession(
        id="session-1",
        title="Chat",
        messages=[
            {"role": "user", "content": "First"},
            {"role": "assistant", "content": "Reply"},
            {"role": "user", "content": "Trailing"},
        ],
        created_at="2026-07-15T00:00:00Z",
        updated_at="2026-07-15T00:00:00Z",
    )

    updated = delete_last_turn(session)

    assert updated.messages == [
        {"role": "user", "content": "First"},
        {"role": "assistant", "content": "Reply"},
    ]


def test_delete_last_turn_is_safe_for_empty_session():
    session = ChatSession(
        id="session-1",
        title="Chat",
        messages=[],
        created_at="2026-07-15T00:00:00Z",
        updated_at="2026-07-15T00:00:00Z",
    )

    assert delete_last_turn(session) == session
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_sessions.py -q --basetemp .pytest_cache/tmp
```

Expected: FAIL during collection with an import error for `delete_last_turn` or `export_sessions_json`.

- [ ] **Step 3: Implement all-session export and last-turn deletion**

Add this helper after `export_session_json` in `ai_chat/sessions.py`:

```python
def export_sessions_json(sessions: list[ChatSession]) -> str:
    payload = {"sessions": [session_to_dict(session) for session in sessions]}
    return json.dumps(payload, ensure_ascii=False, indent=2)
```

Add this helper after `update_session_messages`:

```python
def delete_last_turn(session: ChatSession) -> ChatSession:
    if not session.messages:
        return session

    delete_count = 1
    if (
        len(session.messages) >= 2
        and session.messages[-1].get("role") == "assistant"
        and session.messages[-2].get("role") == "user"
    ):
        delete_count = 2

    return update_session_messages(session, session.messages[:-delete_count])
```

- [ ] **Step 4: Verify helper tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_sessions.py -q --basetemp .pytest_cache/tmp
.\.venv\Scripts\python.exe -m ruff check .
```

Expected:

- `tests/test_sessions.py`: all tests pass.
- Ruff exits 0.

- [ ] **Step 5: Commit Task 4**

Run:

```powershell
git add ai_chat/sessions.py tests/test_sessions.py
git commit -m "feat: add session backup and turn deletion helpers"
```

## Task 5: Wire All-Session Export and Last-Turn Deletion into Streamlit

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Update imports in `app.py`**

Change the `ai_chat.sessions` import block to include:

```python
    delete_last_turn,
    export_sessions_json,
```

The full import block should include all helpers used by v1.5:

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

- [ ] **Step 2: Add `Export All JSON` in `render_sessions_sidebar()`**

After the existing single-session `Export JSON` button, add:

```python
    st.download_button(
        "Export All JSON",
        data=export_sessions_json(st.session_state.sessions),
        file_name="simple-ai-chat-sessions.json",
        mime="application/json",
        use_container_width=True,
    )
```

- [ ] **Step 3: Add `Delete last turn` near `Clear chat`**

In `render_sidebar()`, after the existing `Clear chat` button block, add:

```python
        if active_session().messages and st.button("Delete last turn", use_container_width=True):
            replace_active_session(delete_last_turn(active_session()))
            st.rerun()
```

Keep `Clear chat` unchanged.

- [ ] **Step 4: Run verification**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp .pytest_cache/tmp
.\.venv\Scripts\python.exe -m compileall app.py ai_chat
.\.venv\Scripts\python.exe -m ruff check .
```

Expected:

- pytest exits 0.
- compileall exits 0.
- Ruff exits 0.

- [ ] **Step 5: Commit Task 5**

Run:

```powershell
git add app.py
git commit -m "feat: add all sessions export and turn deletion"
```

## Task 6: Documentation and Final Verification

**Files:**
- Modify: `README.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Update README feature list**

In `README.md`, update the feature list so it includes:

```markdown
- Automatic titles for new chats
- Recent-first session sorting and title search
- JSON import/export for individual chats and all sessions
- Delete the last chat turn
```

Keep existing DeepSeek/OpenAI, streaming, diagnostics, Markdown export, and deployment bullets.

- [ ] **Step 2: Update README Local Sessions section**

Replace the sidebar supports list in `README.md` under `## Local Sessions` with:

```markdown
The sidebar supports:

- Creating a new chat
- Switching chats
- Searching chats by title
- Renaming the active chat
- Deleting the active chat
- Deleting the last turn from the active chat
- Exporting the active chat as JSON
- Exporting all local chats as JSON
- Importing chat sessions from JSON

New chats are automatically titled from the first user prompt unless the chat already has a custom title. The session list is sorted by most recently updated chat first.
```

- [ ] **Step 3: Update CHANGELOG**

Add this entry immediately after `# Changelog`:

```markdown
## v1.5 - Conversation UX

- Added automatic titles for new chats.
- Added recent-first session sorting and title search.
- Added all-session JSON export.
- Added last-turn deletion for the active chat.
```

- [ ] **Step 4: Run final verification**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp .pytest_cache/tmp
.\.venv\Scripts\python.exe -m compileall app.py ai_chat
.\.venv\Scripts\python.exe -m ruff check .
git status --short
```

Expected:

- pytest exits 0.
- compileall exits 0.
- Ruff exits 0.
- `git status --short` shows only `README.md` and `CHANGELOG.md` modified before commit.

- [ ] **Step 5: Commit Task 6**

Run:

```powershell
git add README.md CHANGELOG.md
git commit -m "docs: document conversation ux v1.5"
```

## Task 7: Push v1.5

**Files:**
- No source changes unless final verification finds a defect.

- [ ] **Step 1: Confirm clean state and recent commits**

Run:

```powershell
git status --short
git log --oneline -8
```

Expected:

- `git status --short` is empty.
- Recent commits include v1.5 automatic titles, sorting/search, export/deletion, docs, plus the v1.5 design and plan commits.

- [ ] **Step 2: Push**

Run:

```powershell
git push
```

Expected:

- Local `main` pushes to `origin/main`.
- No extra commit is created for this push-only task.
