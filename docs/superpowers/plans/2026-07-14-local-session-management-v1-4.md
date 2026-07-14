# Local Session Management v1.4 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add local multi-session chat management with JSON persistence, JSON import/export, and sidebar controls.

**Architecture:** Add `ai_chat/sessions.py` as the session domain and storage boundary. Keep `app.py` responsible for Streamlit UI only, using session helpers to load, mutate, save, import, and export active chat sessions.

**Tech Stack:** Python, Streamlit, pytest, Ruff, JSON files under `.data/`.

---

## File Structure

- Create `ai_chat/sessions.py`: session dataclasses, default session creation, mutation helpers, JSON serialization, storage load/save, import/export.
- Create `tests/test_sessions.py`: unit tests for session model, storage, deletion, corruption handling, import, and export.
- Modify `app.py`: replace single `st.session_state.messages` with active session messages and sidebar session controls.
- Modify `.gitignore`: add `.data/`.
- Modify `README.md`: document local session storage and JSON import/export.
- Modify `CHANGELOG.md`: add v1.4 notes.

## Task 1: Session Model and Basic Operations

**Files:**
- Create: `ai_chat/sessions.py`
- Create: `tests/test_sessions.py`

- [ ] **Step 1: Write failing session model tests**

Create `tests/test_sessions.py`:

```python
from ai_chat.sessions import (
    ChatSession,
    create_default_session,
    create_session,
    delete_session,
    rename_session,
)


def test_create_default_session():
    session = create_default_session()

    assert session.title == "Untitled chat"
    assert session.messages == []
    assert session.id
    assert session.created_at
    assert session.updated_at


def test_create_session_uses_title():
    session = create_session("Project notes")

    assert session.title == "Project notes"
    assert session.messages == []


def test_create_session_falls_back_for_empty_title():
    session = create_session("")

    assert session.title == "Untitled chat"


def test_rename_session_updates_title_and_timestamp():
    session = ChatSession(
        id="session-1",
        title="Old",
        messages=[],
        created_at="2026-07-14T00:00:00Z",
        updated_at="2026-07-14T00:00:00Z",
    )

    renamed = rename_session(session, "New")

    assert renamed.id == "session-1"
    assert renamed.title == "New"
    assert renamed.updated_at != "2026-07-14T00:00:00Z"


def test_delete_session_preserves_at_least_one_session():
    only_session = create_session("Only")

    sessions, active_id = delete_session([only_session], only_session.id)

    assert len(sessions) == 1
    assert sessions[0].id == active_id
    assert sessions[0].id != only_session.id


def test_delete_session_selects_remaining_session():
    first = create_session("First")
    second = create_session("Second")

    sessions, active_id = delete_session([first, second], first.id)

    assert sessions == [second]
    assert active_id == second.id
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_sessions.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'ai_chat.sessions'`.

- [ ] **Step 3: Implement session model helpers**

Create `ai_chat/sessions.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4


DEFAULT_TITLE = "Untitled chat"


@dataclass(frozen=True)
class ChatSession:
    id: str
    title: str
    messages: list[dict[str, str]]
    created_at: str
    updated_at: str


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def safe_title(title: str) -> str:
    cleaned = title.strip()
    return cleaned or DEFAULT_TITLE


def create_default_session() -> ChatSession:
    return create_session(DEFAULT_TITLE)


def create_session(title: str) -> ChatSession:
    now = utc_now()
    return ChatSession(
        id=str(uuid4()),
        title=safe_title(title),
        messages=[],
        created_at=now,
        updated_at=now,
    )


def rename_session(session: ChatSession, title: str) -> ChatSession:
    return ChatSession(
        id=session.id,
        title=safe_title(title),
        messages=session.messages,
        created_at=session.created_at,
        updated_at=utc_now(),
    )


def delete_session(sessions: list[ChatSession], session_id: str) -> tuple[list[ChatSession], str]:
    remaining = [session for session in sessions if session.id != session_id]
    if not remaining:
        replacement = create_default_session()
        return [replacement], replacement.id
    return remaining, remaining[0].id
```

- [ ] **Step 4: Verify and commit**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_sessions.py -q
.\.venv\Scripts\python.exe -m ruff check .
```

Expected: both commands exit 0.

Commit:

```powershell
git add ai_chat/sessions.py tests/test_sessions.py
git commit -m "feat: add local chat session model"
```

## Task 2: JSON Storage and Import/Export

**Files:**
- Modify: `ai_chat/sessions.py`
- Modify: `tests/test_sessions.py`
- Modify: `.gitignore`

- [ ] **Step 1: Add failing storage tests**

Append this to `tests/test_sessions.py`:

```python
from pathlib import Path

from ai_chat.sessions import (
    export_session_json,
    import_sessions_json,
    load_sessions,
    save_sessions,
)


def test_save_and_load_sessions(tmp_path):
    path = tmp_path / "chats.json"
    session = create_session("Saved")
    session.messages.append({"role": "user", "content": "Hello"})

    save_sessions(path, [session])
    loaded = load_sessions(path)

    assert loaded == [session]


def test_load_sessions_returns_default_when_file_missing(tmp_path):
    loaded = load_sessions(tmp_path / "missing.json")

    assert len(loaded) == 1
    assert loaded[0].title == "Untitled chat"


def test_load_sessions_backs_up_corrupt_file(tmp_path):
    path = tmp_path / "chats.json"
    path.write_text("{not-json", encoding="utf-8")

    loaded = load_sessions(path)

    assert len(loaded) == 1
    assert (tmp_path / "chats.invalid.json").exists()


def test_export_session_json_round_trips():
    session = create_session("Exported")
    session.messages.append({"role": "assistant", "content": "Hi"})

    exported = export_session_json(session)
    imported = import_sessions_json(exported, existing_ids=set())

    assert len(imported) == 1
    assert imported[0].title == "Exported"
    assert imported[0].messages == [{"role": "assistant", "content": "Hi"}]


def test_import_sessions_json_rejects_invalid_shape():
    assert import_sessions_json('{"bad": true}', existing_ids=set()) == []


def test_import_sessions_json_generates_new_id_on_collision():
    session = create_session("Collision")
    imported = import_sessions_json(export_session_json(session), existing_ids={session.id})

    assert len(imported) == 1
    assert imported[0].id != session.id
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_sessions.py -q
```

Expected: FAIL because storage/import/export helpers are not defined.

- [ ] **Step 3: Implement serialization and storage helpers**

Append this to `ai_chat/sessions.py`:

```python
import json
from pathlib import Path


def session_to_dict(session: ChatSession) -> dict[str, object]:
    return {
        "id": session.id,
        "title": session.title,
        "messages": session.messages,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
    }


def session_from_dict(data: dict[str, object], existing_ids: set[str] | None = None) -> ChatSession | None:
    existing_ids = existing_ids or set()
    raw_messages = data.get("messages", [])
    if not isinstance(raw_messages, list):
        return None
    messages = [
        {"role": str(message.get("role", "")), "content": str(message.get("content", ""))}
        for message in raw_messages
        if isinstance(message, dict) and message.get("role") and message.get("content")
    ]
    now = utc_now()
    session_id = str(data.get("id") or uuid4())
    if session_id in existing_ids:
        session_id = str(uuid4())
    return ChatSession(
        id=session_id,
        title=safe_title(str(data.get("title", ""))),
        messages=messages,
        created_at=str(data.get("created_at") or now),
        updated_at=str(data.get("updated_at") or now),
    )


def save_sessions(path: Path, sessions: list[ChatSession]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"sessions": [session_to_dict(session) for session in sessions]}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_sessions(path: Path) -> list[ChatSession]:
    if not path.exists():
        return [create_default_session()]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        backup = path.with_name(f"{path.stem}.invalid{path.suffix}")
        path.replace(backup)
        return [create_default_session()]
    raw_sessions = payload.get("sessions", []) if isinstance(payload, dict) else []
    sessions = []
    seen_ids: set[str] = set()
    for raw_session in raw_sessions:
        if isinstance(raw_session, dict):
            session = session_from_dict(raw_session, seen_ids)
            if session is not None:
                sessions.append(session)
                seen_ids.add(session.id)
    return sessions or [create_default_session()]


def export_session_json(session: ChatSession) -> str:
    return json.dumps(session_to_dict(session), ensure_ascii=False, indent=2)


def import_sessions_json(text: str, existing_ids: set[str]) -> list[ChatSession]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return []
    raw_sessions = payload.get("sessions") if isinstance(payload, dict) else None
    if raw_sessions is None and isinstance(payload, dict) and "messages" in payload:
        raw_sessions = [payload]
    if not isinstance(raw_sessions, list):
        return []
    imported = []
    seen_ids = set(existing_ids)
    for raw_session in raw_sessions:
        if isinstance(raw_session, dict):
            session = session_from_dict(raw_session, seen_ids)
            if session is not None:
                imported.append(session)
                seen_ids.add(session.id)
    return imported
```

Add this line to `.gitignore`:

```text
.data/
```

- [ ] **Step 4: Verify and commit**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_sessions.py -q
.\.venv\Scripts\python.exe -m ruff check .
git check-ignore .data/chats.json
```

Expected:

- tests pass.
- Ruff passes.
- `git check-ignore` prints `.data/chats.json`.

Commit:

```powershell
git add ai_chat/sessions.py tests/test_sessions.py .gitignore
git commit -m "feat: add local session storage"
```

## Task 3: Streamlit Session Sidebar Integration

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Refactor app state to load sessions**

In `app.py`, import:

```python
from pathlib import Path

from ai_chat.sessions import (
    ChatSession,
    create_session,
    delete_session,
    export_session_json,
    load_sessions,
    rename_session,
    save_sessions,
)
```

Add:

```python
SESSION_STORE = Path(".data/chats.json")
```

Replace the existing `messages` initialization with session initialization:

```python
    if "sessions" not in st.session_state:
        st.session_state.sessions = load_sessions(SESSION_STORE)
        st.session_state.active_session_id = st.session_state.sessions[0].id
```

- [ ] **Step 2: Add active session helpers**

Add to `app.py`:

```python
def active_session() -> ChatSession:
    for session in st.session_state.sessions:
        if session.id == st.session_state.active_session_id:
            return session
    st.session_state.active_session_id = st.session_state.sessions[0].id
    return st.session_state.sessions[0]


def replace_active_session(updated: ChatSession) -> None:
    st.session_state.sessions = [
        updated if session.id == updated.id else session for session in st.session_state.sessions
    ]
    save_sessions(SESSION_STORE, st.session_state.sessions)
```

- [ ] **Step 3: Use active session messages for chat**

In `main()`, set:

```python
    session = active_session()
```

Replace all `st.session_state.messages` reads/writes with `session.messages` and `replace_active_session(...)` after changes. When user/assistant messages are appended, create an updated `ChatSession` preserving metadata and setting `updated_at` through a helper from `sessions.py` if needed.

If the existing helper set is insufficient, add a small `update_session_messages(session, messages)` helper in `ai_chat/sessions.py` and test it in `tests/test_sessions.py` before using it.

- [ ] **Step 4: Add sidebar session controls**

Add a `render_sessions_sidebar()` helper in `app.py` called near the top of `render_sidebar()`:

```python
def render_sessions_sidebar() -> None:
    st.subheader("Sessions")
    labels = {session.title: session.id for session in st.session_state.sessions}
    current = active_session()
    selected_title = st.selectbox("Active chat", options=list(labels), index=list(labels.values()).index(current.id))
    st.session_state.active_session_id = labels[selected_title]

    new_title = st.text_input("Chat title", value=active_session().title)
    if new_title != active_session().title:
        replace_active_session(rename_session(active_session(), new_title))

    if st.button("New chat", use_container_width=True):
        session = create_session("Untitled chat")
        st.session_state.sessions.append(session)
        st.session_state.active_session_id = session.id
        save_sessions(SESSION_STORE, st.session_state.sessions)
        st.rerun()

    if st.button("Delete chat", use_container_width=True):
        sessions, active_id = delete_session(st.session_state.sessions, active_session().id)
        st.session_state.sessions = sessions
        st.session_state.active_session_id = active_id
        save_sessions(SESSION_STORE, st.session_state.sessions)
        st.rerun()
```

- [ ] **Step 5: Verify and commit**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall app.py ai_chat
.\.venv\Scripts\python.exe -m ruff check .
```

Expected: all commands exit 0.

Commit:

```powershell
git add app.py ai_chat/sessions.py tests/test_sessions.py
git commit -m "feat: add local session sidebar"
```

## Task 4: JSON Import and Export UI

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Add JSON export button**

In the sidebar session section, add:

```python
    st.download_button(
        "Export JSON",
        data=export_session_json(active_session()),
        file_name=f"{active_session().title or 'chat'}.json",
        mime="application/json",
        use_container_width=True,
    )
```

- [ ] **Step 2: Add JSON import uploader**

Import:

```python
from ai_chat.sessions import import_sessions_json
```

In the sidebar session section, add:

```python
    uploaded = st.file_uploader("Import JSON", type=["json"])
    if uploaded is not None:
        imported = import_sessions_json(
            uploaded.getvalue().decode("utf-8"),
            existing_ids={session.id for session in st.session_state.sessions},
        )
        if imported:
            st.session_state.sessions.extend(imported)
            st.session_state.active_session_id = imported[0].id
            save_sessions(SESSION_STORE, st.session_state.sessions)
            st.success(f"Imported {len(imported)} session(s).")
            st.rerun()
        else:
            st.error("Invalid chat session JSON.")
```

- [ ] **Step 3: Keep Markdown export on active session**

Update Markdown export to use:

```python
active_session().messages
```

- [ ] **Step 4: Verify and commit**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall app.py ai_chat
.\.venv\Scripts\python.exe -m ruff check .
```

Expected: all commands exit 0.

Commit:

```powershell
git add app.py
git commit -m "feat: add session json import export"
```

## Task 5: Documentation and Final Verification

**Files:**
- Modify: `README.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Update README features**

Add:

```markdown
- Local multi-session management
- JSON session persistence under `.data/`
- JSON import/export for chat sessions
```

- [ ] **Step 2: Add README sessions section**

Add before `## Deployment`:

```markdown
## Local Sessions

The app stores local chat sessions in `.data/chats.json`. The `.data/` directory is ignored by Git so private chat history is not committed.

The sidebar supports:

- Creating a new chat
- Switching chats
- Renaming the active chat
- Deleting the active chat
- Exporting the active chat as JSON
- Importing chat sessions from JSON

Markdown export remains available for human-readable sharing. JSON export is intended for backup and re-import.
```

- [ ] **Step 3: Update CHANGELOG**

Add after `# Changelog`:

```markdown
## v1.4 - Local Session Management

- Added local multi-session management.
- Added JSON persistence under `.data/chats.json`.
- Added JSON import and export for sessions.
- Kept Markdown export for readable sharing.
```

- [ ] **Step 4: Full verification**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall app.py ai_chat
.\.venv\Scripts\python.exe -m ruff check .
git check-ignore .data/chats.json
git status --short
```

Expected:

- tests pass.
- compileall passes.
- Ruff passes.
- `git check-ignore` prints `.data/chats.json`.
- status shows only README/CHANGELOG changes before commit.

Commit:

```powershell
git add README.md CHANGELOG.md
git commit -m "docs: document local session management v1.4"
```

## Task 6: Push

**Files:**
- No code changes unless final verification reveals a defect.

- [ ] **Step 1: Verify clean state and recent commits**

Run:

```powershell
git status --short
git log --oneline -8
```

Expected:

- `git status --short`: empty.
- recent commits include v1.4 session model, storage, sidebar, import/export, and docs commits.

- [ ] **Step 2: Push**

Run:

```powershell
git push
```

Expected: local `main` pushes to `origin/main`.
