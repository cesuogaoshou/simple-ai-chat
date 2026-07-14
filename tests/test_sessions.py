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
