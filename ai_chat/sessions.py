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


def delete_session(
    sessions: list[ChatSession], session_id: str
) -> tuple[list[ChatSession], str]:
    remaining = [session for session in sessions if session.id != session_id]
    if not remaining:
        replacement = create_default_session()
        return [replacement], replacement.id
    return remaining, remaining[0].id
