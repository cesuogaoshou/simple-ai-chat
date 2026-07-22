# Session Management v1.10 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add safer and more useful local session management with stable sidebar filters, filtered JSON export, batch tag operations, and delete confirmation.

**Architecture:** Keep local session behavior in `ai_chat.sessions` as pure, tested helpers, and keep Streamlit-specific behavior in `app.py`. Reuse the current JSON export shape so filtered exports and imported backups stay compatible with existing session import paths. Preserve the local-first `.data/chats.json` storage model and avoid account, database, cloud sync, or frontend redesign work.

**Tech Stack:** Python 3.13, Streamlit, pytest, Ruff, local JSON storage.

---

## File Structure

- Modify `ai_chat/sessions.py`: add a combined visible-session filter helper and batch tag mutation helpers.
- Modify `tests/test_sessions.py`: add unit coverage for visible-session filtering and batch tag helpers.
- Modify `app.py`: give sidebar filter widgets explicit keys, add filtered JSON export, add batch tag controls for the current filtered results, and add delete confirmation.
- Modify `README.md`: document filtered JSON export, batch tag operations, and delete confirmation.
- Modify `CHANGELOG.md`: add v1.10 release notes.

Use this verification command shape in this workspace:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp .pytest_cache/tmp
.\.venv\Scripts\python.exe -m compileall app.py ai_chat
.\.venv\Scripts\python.exe -m ruff check .
```

The `--basetemp .pytest_cache/tmp` flag keeps pytest temporary files inside the repository on Windows.

## Task 1: Stable Sidebar Filter State

**Files:**
- Modify: `ai_chat/sessions.py`
- Modify: `tests/test_sessions.py`
- Modify: `app.py`

- [ ] **Step 1: Write failing visible filter tests**

In `tests/test_sessions.py`, update the import block to include:

```python
    filter_visible_sessions,
```

After `test_filter_sessions_by_tag_returns_all_for_blank_tag`, add:

```python
def test_filter_visible_sessions_applies_search_then_tag_filter():
    first = ChatSession(
        id="first",
        title="Release planning",
        messages=[{"role": "assistant", "content": "Prepare launch notes"}],
        created_at="2026-07-16T00:00:00Z",
        updated_at="2026-07-16T00:00:00Z",
        tags=["work"],
    )
    second = ChatSession(
        id="second",
        title="Release bug",
        messages=[{"role": "user", "content": "Investigate provider issue"}],
        created_at="2026-07-16T00:00:00Z",
        updated_at="2026-07-16T00:00:00Z",
        tags=["bug"],
    )
    third = ChatSession(
        id="third",
        title="Personal notes",
        messages=[{"role": "user", "content": "Release reading list"}],
        created_at="2026-07-16T00:00:00Z",
        updated_at="2026-07-16T00:00:00Z",
        tags=["personal"],
    )

    assert filter_visible_sessions([first, second, third], "release", "bug") == [second]


def test_filter_visible_sessions_returns_all_for_blank_filters():
    first = create_session("First")
    second = create_session("Second")

    assert filter_visible_sessions([first, second], "   ", "   ") == [first, second]
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_sessions.py -q --basetemp .pytest_cache/tmp
```

Expected: FAIL because `filter_visible_sessions` does not exist yet.

- [ ] **Step 3: Implement the visible filter helper**

In `ai_chat/sessions.py`, after `filter_sessions_by_tag`, add:

```python
def filter_visible_sessions(
    sessions: list[ChatSession],
    query: str,
    tag: str,
) -> list[ChatSession]:
    return filter_sessions_by_tag(search_sessions(sessions, query), tag)
```

- [ ] **Step 4: Wire explicit Streamlit keys**

In `app.py`, add `filter_visible_sessions` to the `ai_chat.sessions` import list.

In `main()`, after `custom_preset_name` initialization, add:

```python
    if "session_search_query" not in st.session_state:
        st.session_state.session_search_query = ""
    if "session_tag_filter" not in st.session_state:
        st.session_state.session_tag_filter = "All tags"
```

In `render_sessions_sidebar()`, replace:

```python
    query = st.text_input("Search chats", value="")
    tag_options = ["All tags", *list_session_tags(st.session_state.sessions)]
    selected_tag = st.selectbox("Filter tag", options=tag_options)
    tag_filter = "" if selected_tag == "All tags" else selected_tag
    visible_sessions = filter_sessions_by_tag(
        search_sessions(st.session_state.sessions, query),
        tag_filter,
    )
```

with:

```python
    query = st.text_input("Search chats", key="session_search_query")
    tag_options = ["All tags", *list_session_tags(st.session_state.sessions)]
    if st.session_state.session_tag_filter not in tag_options:
        st.session_state.session_tag_filter = "All tags"
    selected_tag = st.selectbox(
        "Filter tag",
        options=tag_options,
        key="session_tag_filter",
    )
    tag_filter = "" if selected_tag == "All tags" else selected_tag
    visible_sessions = filter_visible_sessions(
        st.session_state.sessions,
        query,
        tag_filter,
    )
```

- [ ] **Step 5: Run task verification**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_sessions.py -q --basetemp .pytest_cache/tmp
.\.venv\Scripts\python.exe -m compileall app.py ai_chat
.\.venv\Scripts\python.exe -m ruff check .
```

Expected:

- `tests/test_sessions.py` passes.
- compile command succeeds.
- Ruff reports `All checks passed!`.

- [ ] **Step 6: Commit Task 1**

Run:

```powershell
git status --short
git add ai_chat/sessions.py tests/test_sessions.py app.py
git diff --cached --check
git commit -m "feat: stabilize session sidebar filters"
```

Expected: commit succeeds with only `ai_chat/sessions.py`, `tests/test_sessions.py`, and `app.py` staged.

## Task 2: Filtered Session JSON Export

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Add filtered export button**

In `render_sessions_sidebar()`, after the existing `Export All JSON` download button:

```python
    st.download_button(
        "Export All JSON",
        data=export_sessions_json(st.session_state.sessions),
        file_name="simple-ai-chat-sessions.json",
        mime="application/json",
        use_container_width=True,
    )
```

add:

```python
    if visible_sessions:
        st.download_button(
            "Export Filtered JSON",
            data=export_sessions_json(visible_sessions),
            file_name="simple-ai-chat-filtered-sessions.json",
            mime="application/json",
            use_container_width=True,
        )
    else:
        st.caption("Filtered JSON export is unavailable because no chats match.")
```

- [ ] **Step 2: Run focused verification**

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

- [ ] **Step 3: Commit Task 2**

Run:

```powershell
git status --short
git add app.py
git diff --cached --check
git commit -m "feat: export filtered chat sessions"
```

Expected: commit succeeds with only `app.py` staged.

## Task 3: Batch Tag Helpers

**Files:**
- Modify: `ai_chat/sessions.py`
- Modify: `tests/test_sessions.py`

- [ ] **Step 1: Write failing batch tag tests**

In `tests/test_sessions.py`, update the import block to include:

```python
    add_tag_to_sessions,
    remove_tag_from_sessions,
```

After `test_filter_visible_sessions_returns_all_for_blank_filters`, add:

```python
def test_add_tag_to_sessions_adds_tag_to_selected_sessions_only():
    first = ChatSession(
        id="first",
        title="First",
        messages=[],
        created_at="2026-07-16T00:00:00Z",
        updated_at="2026-07-16T00:00:00Z",
        tags=["work"],
    )
    second = ChatSession(
        id="second",
        title="Second",
        messages=[],
        created_at="2026-07-16T00:00:00Z",
        updated_at="2026-07-16T00:00:00Z",
        tags=["research"],
    )

    updated = add_tag_to_sessions([first, second], {"first"}, "bug")

    assert updated[0].tags == ["work", "bug"]
    assert updated[0].updated_at != "2026-07-16T00:00:00Z"
    assert updated[1] == second


def test_add_tag_to_sessions_ignores_blank_and_duplicate_tags():
    session = ChatSession(
        id="session-1",
        title="Tagged",
        messages=[],
        created_at="2026-07-16T00:00:00Z",
        updated_at="2026-07-16T00:00:00Z",
        tags=["Work"],
    )

    assert add_tag_to_sessions([session], {"session-1"}, "   ") == [session]
    assert add_tag_to_sessions([session], {"session-1"}, "work") == [session]


def test_remove_tag_from_sessions_removes_case_insensitive_tag_from_selected_sessions_only():
    first = ChatSession(
        id="first",
        title="First",
        messages=[],
        created_at="2026-07-16T00:00:00Z",
        updated_at="2026-07-16T00:00:00Z",
        tags=["Work", "bug"],
    )
    second = ChatSession(
        id="second",
        title="Second",
        messages=[],
        created_at="2026-07-16T00:00:00Z",
        updated_at="2026-07-16T00:00:00Z",
        tags=["Work"],
    )

    updated = remove_tag_from_sessions([first, second], {"first"}, "work")

    assert updated[0].tags == ["bug"]
    assert updated[0].updated_at != "2026-07-16T00:00:00Z"
    assert updated[1] == second


def test_remove_tag_from_sessions_ignores_blank_or_missing_tags():
    session = ChatSession(
        id="session-1",
        title="Tagged",
        messages=[],
        created_at="2026-07-16T00:00:00Z",
        updated_at="2026-07-16T00:00:00Z",
        tags=["work"],
    )

    assert remove_tag_from_sessions([session], {"session-1"}, "   ") == [session]
    assert remove_tag_from_sessions([session], {"session-1"}, "missing") == [session]
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_sessions.py -q --basetemp .pytest_cache/tmp
```

Expected: FAIL because `add_tag_to_sessions` and `remove_tag_from_sessions` do not exist yet.

- [ ] **Step 3: Implement batch tag helpers**

In `ai_chat/sessions.py`, after `update_session_note`, add:

```python
def replace_session_tags(session: ChatSession, tags: list[str]) -> ChatSession:
    cleaned_tags = clean_tags(tags)
    if cleaned_tags == session.tags:
        return session
    return ChatSession(
        id=session.id,
        title=session.title,
        messages=session.messages,
        created_at=session.created_at,
        updated_at=utc_now(),
        pinned=session.pinned,
        tags=cleaned_tags,
        note=session.note,
    )


def add_tag_to_sessions(
    sessions: list[ChatSession],
    session_ids: set[str],
    tag: str,
) -> list[ChatSession]:
    cleaned = clean_tags([tag])
    if not cleaned or not session_ids:
        return sessions

    tag_to_add = cleaned[0]
    return [
        replace_session_tags(session, [*session.tags, tag_to_add])
        if session.id in session_ids
        else session
        for session in sessions
    ]


def remove_tag_from_sessions(
    sessions: list[ChatSession],
    session_ids: set[str],
    tag: str,
) -> list[ChatSession]:
    cleaned = clean_tags([tag])
    if not cleaned or not session_ids:
        return sessions

    tag_to_remove = cleaned[0].casefold()
    return [
        replace_session_tags(
            session,
            [existing for existing in session.tags if existing.casefold() != tag_to_remove],
        )
        if session.id in session_ids
        else session
        for session in sessions
    ]
```

- [ ] **Step 4: Run task verification**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_sessions.py -q --basetemp .pytest_cache/tmp
.\.venv\Scripts\python.exe -m compileall app.py ai_chat
.\.venv\Scripts\python.exe -m ruff check .
```

Expected:

- `tests/test_sessions.py` passes.
- compile command succeeds.
- Ruff reports `All checks passed!`.

- [ ] **Step 5: Commit Task 3**

Run:

```powershell
git status --short
git add ai_chat/sessions.py tests/test_sessions.py
git diff --cached --check
git commit -m "feat: add batch session tag helpers"
```

Expected: commit succeeds with only `ai_chat/sessions.py` and `tests/test_sessions.py` staged.

## Task 4: Batch Tag Sidebar Controls

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Update session imports**

In `app.py`, add these imports from `ai_chat.sessions`:

```python
    add_tag_to_sessions,
    remove_tag_from_sessions,
```

- [ ] **Step 2: Initialize batch tag input state**

In `main()`, after the `session_tag_filter` initialization, add:

```python
    if "session_batch_tag" not in st.session_state:
        st.session_state.session_batch_tag = ""
```

- [ ] **Step 3: Add batch tag controls**

In `render_sessions_sidebar()`, after the block that computes `visible_ids`:

```python
    visible_ids = [session.id for session in visible_sessions]
```

add:

```python
    st.caption(f"{len(visible_sessions)} matching chat(s).")
    batch_tag = st.text_input("Batch tag", key="session_batch_tag")
    has_batch_tag = bool(normalize_session_tags(batch_tag))
    can_batch_update = bool(visible_sessions) and has_batch_tag
    if st.button(
        "Add tag to filtered chats",
        disabled=not can_batch_update,
        use_container_width=True,
    ):
        st.session_state.sessions = sort_sessions(
            add_tag_to_sessions(
                st.session_state.sessions,
                set(visible_ids),
                batch_tag,
            )
        )
        save_sessions(SESSION_STORE, st.session_state.sessions)
        st.rerun()
    if st.button(
        "Remove tag from filtered chats",
        disabled=not can_batch_update,
        use_container_width=True,
    ):
        st.session_state.sessions = sort_sessions(
            remove_tag_from_sessions(
                st.session_state.sessions,
                set(visible_ids),
                batch_tag,
            )
        )
        save_sessions(SESSION_STORE, st.session_state.sessions)
        st.rerun()
```

The controls operate on the current search and tag-filter result set because `visible_ids` is computed from `visible_sessions`.

- [ ] **Step 4: Run full verification**

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

- [ ] **Step 5: Commit Task 4**

Run:

```powershell
git status --short
git add app.py
git diff --cached --check
git commit -m "feat: add batch tag controls"
```

Expected: commit succeeds with only `app.py` staged.

## Task 5: Delete Confirmation and Documentation

**Files:**
- Modify: `app.py`
- Modify: `README.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Initialize delete confirmation state**

In `main()`, after `session_batch_tag` initialization, add:

```python
    if "confirm_delete_active_chat" not in st.session_state:
        st.session_state.confirm_delete_active_chat = False
```

- [ ] **Step 2: Require confirmation before deleting the active chat**

In `render_sessions_sidebar()`, replace:

```python
    if st.button("Delete chat", use_container_width=True):
        sessions, active_id = delete_session(st.session_state.sessions, active_session().id)
        st.session_state.sessions = sessions
        st.session_state.active_session_id = active_id
        st.session_state.sessions = sort_sessions(st.session_state.sessions)
        save_sessions(SESSION_STORE, st.session_state.sessions)
        st.rerun()
```

with:

```python
    st.checkbox("Confirm delete active chat", key="confirm_delete_active_chat")
    if st.button(
        "Delete chat",
        disabled=not st.session_state.confirm_delete_active_chat,
        use_container_width=True,
    ):
        sessions, active_id = delete_session(st.session_state.sessions, active_session().id)
        st.session_state.sessions = sort_sessions(sessions)
        st.session_state.active_session_id = active_id
        st.session_state.confirm_delete_active_chat = False
        save_sessions(SESSION_STORE, st.session_state.sessions)
        st.rerun()
```

- [ ] **Step 3: Update README feature list**

In `README.md`, update the features list by adding these bullets near the existing session-management bullets:

```markdown
- Filtered JSON export for matching chats
- Batch tag add/remove for filtered chats
- Delete confirmation for active chat deletion
```

- [ ] **Step 4: Update README Local Sessions section**

In `README.md`, in the list under `The sidebar supports:`, add:

```markdown
- Exporting filtered chats as JSON
- Adding or removing a tag across filtered chats
- Confirming before deleting the active chat
```

After the paragraph that starts with `Chat tags and notes are stored`, add:

```markdown
Filtered JSON export downloads the current search and tag-filter result set using the same session JSON shape as all-session export, so the file can be imported again. Batch tag controls also operate on the current filtered result set.

Deleting the active chat requires selecting `Confirm delete active chat` first. If the last remaining chat is deleted, the app creates a new empty default chat automatically.
```

- [ ] **Step 5: Add changelog entry**

At the top of `CHANGELOG.md`, after `# Changelog`, add:

```markdown
## v1.10 - Session Management Reliability

- Added stable sidebar filter widget keys.
- Added filtered chat session JSON export.
- Added batch tag add and remove operations for filtered chats.
- Added confirmation before deleting the active chat.
```

- [ ] **Step 6: Run full verification**

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
- `git diff --check` prints no whitespace errors.

- [ ] **Step 7: Commit Task 5**

Run:

```powershell
git status --short
git add app.py README.md CHANGELOG.md
git diff --cached --check
git commit -m "feat: confirm destructive chat deletion"
```

Expected: commit succeeds with only `app.py`, `README.md`, and `CHANGELOG.md` staged.

## Task 6: Final Version Verification and Push

**Files:**
- No planned file edits.

- [ ] **Step 1: Run final verification**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp .pytest_cache/tmp
.\.venv\Scripts\python.exe -m compileall app.py ai_chat
.\.venv\Scripts\python.exe -m ruff check .
git status --short --branch
git log --oneline origin/main..HEAD
```

Expected:

- pytest reports all tests passing.
- compile command succeeds.
- Ruff reports `All checks passed!`.
- working tree is clean.
- recent commits include v1.10 task commits.

- [ ] **Step 2: Push v1.10**

Run:

```powershell
git push
```

Expected: local `main` pushes to `origin/main`.

## Success Criteria

- Search and tag filter widgets keep their state across Streamlit reruns caused by title, tag, note, pin, import, delete, and batch operations.
- `Export Filtered JSON` downloads exactly the currently visible sessions after search and tag filtering.
- Filtered JSON exports can be imported through the existing JSON import control.
- Batch tag add/remove affects only the currently filtered sessions.
- Blank batch tag input cannot mutate sessions.
- Duplicate tag addition does not create duplicate tags.
- Tag removal is case-insensitive.
- Deleting the active chat requires explicit confirmation.
- Deleting the final remaining chat still leaves the app with a default empty chat.
- Existing provider, streaming, prompt preset, custom preset, pinned session, search, tag filter, Markdown export, and JSON import/export behavior remains intact.
- All tests, compile checks, Ruff checks, and whitespace checks pass.
