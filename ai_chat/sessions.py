from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
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


def update_session_messages(
    session: ChatSession, messages: list[dict[str, str]]
) -> ChatSession:
    return ChatSession(
        id=session.id,
        title=session.title,
        messages=messages,
        created_at=session.created_at,
        updated_at=utc_now(),
    )


def delete_session(
    sessions: list[ChatSession], session_id: str
) -> tuple[list[ChatSession], str]:
    remaining = [session for session in sessions if session.id != session_id]
    if not remaining:
        replacement = create_default_session()
        return [replacement], replacement.id
    return remaining, remaining[0].id


def session_to_dict(session: ChatSession) -> dict[str, object]:
    return {
        "id": session.id,
        "title": session.title,
        "messages": session.messages,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
    }


def session_from_dict(
    data: dict[str, object], existing_ids: set[str] | None = None
) -> ChatSession | None:
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
