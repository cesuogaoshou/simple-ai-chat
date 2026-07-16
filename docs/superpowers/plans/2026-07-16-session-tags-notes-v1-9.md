# Session Tags and Notes v1.9 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add local session tags, notes, and tag filtering while preserving existing chat JSON compatibility.

**Architecture:** Extend `ai_chat.sessions` with persisted `tags` and `note` metadata plus pure helpers for normalization, formatting, updating, listing, and filtering. Wire those helpers into the existing Streamlit Sessions sidebar without changing chat request construction or message export behavior.

**Tech Stack:** Python, Streamlit, pytest, Ruff, local JSON storage.

---

## File Structure

- Modify `ai_chat/sessions.py`: add `tags` and `note` fields, preserve them across mutations, parse them during load/import, export them to JSON, and add tag/note helper functions.
- Modify `tests/test_sessions.py`: add unit tests for model compatibility, tag normalization, note handling, metadata preservation, tag listing, and tag filtering.
- Modify `app.py`: add tag filter, `Chat tags` input, and `Chat note` text area in the Sessions sidebar.
- Modify `README.md`: document tags, notes, tag filtering, and JSON compatibility.
- Modify `CHANGELOG.md`: add v1.9 release notes.

Use this verification command shape in this workspace:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp .pytest_cache/tmp
.\.venv\Scripts\python.exe -m compileall app.py ai_chat
.\.venv\Scripts\python.exe -m ruff check .
```

## Task 1: Session Tags and Note Model

**Files:**
- Modify: `ai_chat/sessions.py`
- Modify: `tests/test_sessions.py`

- [ ] **Step 1: Write failing metadata model tests**

In `tests/test_sessions.py`, add assertions to `test_create_default_session_is_unpinned`:

```python
    assert session.tags == []
    assert session.note == ""
```

Add assertions to `test_create_session_is_unpinned`:

```python
    assert session.tags == []
    assert session.note == ""
```

After `test_session_mutations_preserve_pinned_state`, add:

```python
def test_session_mutations_preserve_tags_and_note():
    session = ChatSession(
        id="session-1",
        title="Untitled chat",
        messages=[{"role": "user", "content": "Hello"}],
        created_at="2026-07-15T00:00:00Z",
        updated_at="2026-07-15T00:00:00Z",
        pinned=True,
        tags=["work", "bug"],
        note="Needs follow-up.",
    )

    titled = maybe_auto_title_session(session, "Explain local storage")
    renamed = rename_session(session, "Pinned notes")
    updated = update_session_messages(
        session,
        [{"role": "user", "content": "Updated"}],
    )
    pinned = set_session_pinned(session, False)
    trimmed = delete_last_turn(session)

    for changed in [titled, renamed, updated, pinned, trimmed]:
        assert changed.tags == ["work", "bug"]
        assert changed.note == "Needs follow-up."
```

After `test_session_from_json_uses_false_for_invalid_pinned`, add:

```python
def test_session_from_old_json_defaults_tags_and_note(tmp_path):
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

    assert loaded[0].tags == []
    assert loaded[0].note == ""


def test_session_from_json_cleans_tags_and_note(tmp_path):
    path = tmp_path / "chats.json"
    payload = {
        "sessions": [
            {
                "id": "session-1",
                "title": "Tagged",
                "messages": [],
                "created_at": "2026-07-15T00:00:00Z",
                "updated_at": "2026-07-15T00:00:00Z",
                "tags": [" work ", "", "Bug", "work"],
                "note": " Follow up ",
            }
        ]
    }
    path.write_text(json.dumps(payload), encoding="utf-8")

    loaded = load_sessions(path)

    assert loaded[0].tags == ["work", "Bug"]
    assert loaded[0].note == " Follow up "


def test_session_from_json_uses_empty_tags_for_invalid_tags(tmp_path):
    path = tmp_path / "chats.json"
    payload = {
        "sessions": [
            {
                "id": "session-1",
                "title": "Invalid tags",
                "messages": [],
                "created_at": "2026-07-15T00:00:00Z",
                "updated_at": "2026-07-15T00:00:00Z",
                "tags": "work",
                "note": 123,
            }
        ]
    }
    path.write_text(json.dumps(payload), encoding="utf-8")

    loaded = load_sessions(path)

    assert loaded[0].tags == []
    assert loaded[0].note == "123"
```

After `test_session_json_includes_pinned_state`, add:

```python
def test_session_json_includes_tags_and_note():
    session = ChatSession(
        id="session-1",
        title="Tagged",
        messages=[],
        created_at="2026-07-15T00:00:00Z",
        updated_at="2026-07-15T00:00:00Z",
        tags=["work"],
        note="Important context.",
    )

    exported = json.loads(export_session_json(session))

    assert session_to_dict(session)["tags"] == ["work"]
    assert session_to_dict(session)["note"] == "Important context."
    assert exported["tags"] == ["work"]
    assert exported["note"] == "Important context."
```

After `test_import_session_json_preserves_pinned_state`, add:

```python
def test_import_session_json_preserves_tags_and_note():
    session = ChatSession(
        id="session-1",
        title="Tagged",
        messages=[],
        created_at="2026-07-15T00:00:00Z",
        updated_at="2026-07-15T00:00:00Z",
        tags=["work"],
        note="Important context.",
    )

    imported = import_sessions_json(export_session_json(session), existing_ids=set())

    assert imported[0].tags == ["work"]
    assert imported[0].note == "Important context."
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_sessions.py -q --basetemp .pytest_cache/tmp
```

Expected: FAIL because `ChatSession` has no `tags` or `note` fields yet.

- [ ] **Step 3: Implement metadata fields and JSON compatibility**

In `ai_chat/sessions.py`, update the dataclass import:

```python
from dataclasses import dataclass, field
```

Update `ChatSession`:

```python
@dataclass(frozen=True)
class ChatSession:
    id: str
    title: str
    messages: list[dict[str, str]]
    created_at: str
    updated_at: str
    pinned: bool = False
    tags: list[str] = field(default_factory=list)
    note: str = ""
```

Add this helper after `safe_title`:

```python
def clean_tags(tags: list[object]) -> list[str]:
    cleaned_tags = []
    seen = set()
    for tag in tags:
        cleaned = str(tag).strip()
        folded = cleaned.casefold()
        if cleaned and folded not in seen:
            cleaned_tags.append(cleaned)
            seen.add(folded)
    return cleaned_tags
```

In `maybe_auto_title_session`, `rename_session`, `update_session_messages`, and `set_session_pinned`, pass through:

```python
        tags=session.tags,
        note=session.note,
```

In `session_to_dict`, add:

```python
        "tags": session.tags,
        "note": session.note,
```

In `session_from_dict`, after pinned parsing, add:

```python
    raw_tags = data.get("tags", [])
    tags = clean_tags(raw_tags) if isinstance(raw_tags, list) else []
    note = data.get("note", "")
```

Then pass to `ChatSession`:

```python
        tags=tags,
        note=note if isinstance(note, str) else str(note),
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
git commit -m "feat: add session tags and note fields"
```

Expected: commit succeeds with only `ai_chat/sessions.py` and `tests/test_sessions.py` staged.

## Task 2: Tag and Note Helpers

**Files:**
- Modify: `ai_chat/sessions.py`
- Modify: `tests/test_sessions.py`

- [ ] **Step 1: Write failing helper tests**

In the `tests/test_sessions.py` import block, add:

```python
    format_session_tags,
    list_session_tags,
    normalize_session_tags,
    update_session_note,
    update_session_tags,
```

After the existing tag metadata tests, add:

```python
def test_normalize_session_tags_splits_cleans_and_deduplicates():
    assert normalize_session_tags(" work, bug, Work, , research ") == [
        "work",
        "bug",
        "research",
    ]


def test_format_session_tags_joins_tags_for_display():
    assert format_session_tags(["work", "bug"]) == "work, bug"


def test_update_session_tags_preserves_metadata_and_updates_timestamp():
    session = ChatSession(
        id="session-1",
        title="Tagged",
        messages=[],
        created_at="2026-07-15T00:00:00Z",
        updated_at="2026-07-15T00:00:00Z",
        pinned=True,
        tags=["old"],
        note="Keep note.",
    )

    updated = update_session_tags(session, ["work", "bug"])

    assert updated.tags == ["work", "bug"]
    assert updated.note == "Keep note."
    assert updated.pinned is True
    assert updated.updated_at != "2026-07-15T00:00:00Z"


def test_update_session_note_strips_outer_whitespace_and_updates_timestamp():
    session = ChatSession(
        id="session-1",
        title="Tagged",
        messages=[],
        created_at="2026-07-15T00:00:00Z",
        updated_at="2026-07-15T00:00:00Z",
        tags=["work"],
    )

    updated = update_session_note(session, " Follow up ")

    assert updated.tags == ["work"]
    assert updated.note == "Follow up"
    assert updated.updated_at != "2026-07-15T00:00:00Z"


def test_list_session_tags_returns_unique_sorted_tags():
    first = ChatSession(
        id="first",
        title="First",
        messages=[],
        created_at="2026-07-15T00:00:00Z",
        updated_at="2026-07-15T00:00:00Z",
        tags=["work", "Bug"],
    )
    second = ChatSession(
        id="second",
        title="Second",
        messages=[],
        created_at="2026-07-15T00:00:00Z",
        updated_at="2026-07-15T00:00:00Z",
        tags=["bug", "research"],
    )

    assert list_session_tags([first, second]) == ["Bug", "research", "work"]
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_sessions.py -q --basetemp .pytest_cache/tmp
```

Expected: FAIL because the helper functions do not exist yet.

- [ ] **Step 3: Implement tag and note helpers**

In `ai_chat/sessions.py`, after `clean_tags`, add:

```python
def normalize_session_tags(text: str) -> list[str]:
    return clean_tags(text.split(","))


def format_session_tags(tags: list[str]) -> str:
    return ", ".join(tags)
```

After `set_session_pinned`, add:

```python
def update_session_tags(session: ChatSession, tags: list[str]) -> ChatSession:
    return ChatSession(
        id=session.id,
        title=session.title,
        messages=session.messages,
        created_at=session.created_at,
        updated_at=utc_now(),
        pinned=session.pinned,
        tags=clean_tags(tags),
        note=session.note,
    )


def update_session_note(session: ChatSession, note: str) -> ChatSession:
    return ChatSession(
        id=session.id,
        title=session.title,
        messages=session.messages,
        created_at=session.created_at,
        updated_at=utc_now(),
        pinned=session.pinned,
        tags=session.tags,
        note=note.strip(),
    )
```

After `filter_sessions_by_title`, add:

```python
def list_session_tags(sessions: list[ChatSession]) -> list[str]:
    tags_by_key = {}
    for session in sessions:
        for tag in session.tags:
            tags_by_key.setdefault(tag.casefold(), tag)
    return sorted(tags_by_key.values(), key=str.casefold)
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
git commit -m "feat: add session tag and note helpers"
```

Expected: commit succeeds with only `ai_chat/sessions.py` and `tests/test_sessions.py` staged.

## Task 3: Tag Filtering

**Files:**
- Modify: `ai_chat/sessions.py`
- Modify: `tests/test_sessions.py`

- [ ] **Step 1: Write failing tag filtering tests**

In the `tests/test_sessions.py` import block, add:

```python
    filter_sessions_by_tag,
```

After `test_list_session_tags_returns_unique_sorted_tags`, add:

```python
def test_filter_sessions_by_tag_matches_case_insensitive_tag():
    first = ChatSession(
        id="first",
        title="First",
        messages=[],
        created_at="2026-07-15T00:00:00Z",
        updated_at="2026-07-15T00:00:00Z",
        tags=["Work"],
    )
    second = ChatSession(
        id="second",
        title="Second",
        messages=[],
        created_at="2026-07-15T00:00:00Z",
        updated_at="2026-07-15T00:00:00Z",
        tags=["research"],
    )

    assert filter_sessions_by_tag([first, second], "work") == [first]


def test_filter_sessions_by_tag_returns_all_for_blank_tag():
    first = create_session("First")
    second = create_session("Second")

    assert filter_sessions_by_tag([first, second], "   ") == [first, second]
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_sessions.py -q --basetemp .pytest_cache/tmp
```

Expected: FAIL because `filter_sessions_by_tag` does not exist yet.

- [ ] **Step 3: Implement tag filtering**

In `ai_chat/sessions.py`, after `list_session_tags`, add:

```python
def filter_sessions_by_tag(
    sessions: list[ChatSession], tag: str
) -> list[ChatSession]:
    cleaned = tag.strip().casefold()
    if not cleaned:
        return sessions
    return [
        session
        for session in sessions
        if any(existing.casefold() == cleaned for existing in session.tags)
    ]
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
git commit -m "feat: filter chat sessions by tag"
```

Expected: commit succeeds with only `ai_chat/sessions.py` and `tests/test_sessions.py` staged.

## Task 4: Streamlit Sidebar Tag and Note Controls

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Update session imports**

In `app.py`, add these imports from `ai_chat.sessions`:

```python
    filter_sessions_by_tag,
    format_session_tags,
    list_session_tags,
    normalize_session_tags,
    update_session_note,
    update_session_tags,
```

- [ ] **Step 2: Add tag filter to Sessions sidebar**

In `render_sessions_sidebar()`, after:

```python
    query = st.text_input("Search chats", value="")
    visible_sessions = search_sessions(st.session_state.sessions, query)
```

replace it with:

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

- [ ] **Step 3: Add active session tag and note editors**

In `render_sessions_sidebar()`, after the pin/unpin button block, add:

```python
    tag_text = st.text_input("Chat tags", value=format_session_tags(current.tags))
    updated_tags = normalize_session_tags(tag_text)
    if updated_tags != current.tags:
        replace_active_session(update_session_tags(current, updated_tags))
        st.rerun()

    note = st.text_area("Chat note", value=current.note)
    if note.strip() != current.note:
        replace_active_session(update_session_note(current, note))
        st.rerun()
```

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
git commit -m "feat: add session tag and note controls"
```

Expected: commit succeeds with only `app.py` staged.

## Task 5: Documentation and Push

**Files:**
- Modify: `README.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Update README feature bullets**

In `README.md`, update the feature bullet:

```markdown
- Pinned sessions, recent-first sorting, and title/message search
```

to:

```markdown
- Pinned sessions, tags, notes, recent-first sorting, and title/message search
```

- [ ] **Step 2: Update README Local Sessions section**

In `README.md`, in the list under `The sidebar supports:`, add:

```markdown
- Editing chat tags and notes
- Filtering chats by tag
```

After the paragraph about `Search chats`, add:

```markdown
Chat tags and notes are stored in `.data/chats.json`. Older chat JSON files that do not include tags or notes still load and import with empty metadata.
```

- [ ] **Step 3: Add changelog entry**

At the top of `CHANGELOG.md`, after `# Changelog`, add:

```markdown
## v1.9 - Session Tags and Notes

- Added local chat session tags.
- Added local chat session notes.
- Added tag filtering in the Sessions sidebar.
- Kept old chat JSON compatible by defaulting missing tags and notes to empty metadata.
```

- [ ] **Step 4: Run full verification**

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

- [ ] **Step 5: Commit Task 5 docs**

Run:

```powershell
git status --short
git add README.md CHANGELOG.md
git diff --cached --check
git commit -m "docs: document session tags and notes v1.9"
```

Expected: commit succeeds with only `README.md` and `CHANGELOG.md` staged.

- [ ] **Step 6: Push v1.9**

Run:

```powershell
git status --short --branch
git log --oneline origin/main..HEAD
git push
```

Expected:

- working tree is clean before push.
- recent commits include v1.9 design, v1.9 plan, tags/note model, helpers, tag filtering, Streamlit wiring, and docs.
- local `main` pushes to `origin/main`.
