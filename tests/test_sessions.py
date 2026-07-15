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


def test_derive_session_title_cleans_whitespace():
    assert derive_session_title("  Build   a  small app  ") == "Build a small app"


def test_derive_session_title_truncates_long_prompt():
    title = derive_session_title("1234567890 1234567890 1234567890 extra")

    assert title == "1234567890 1234567890 12345678"
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


def test_update_session_messages_preserves_metadata_and_updates_timestamp():
    session = ChatSession(
        id="session-1",
        title="Chat",
        messages=[],
        created_at="2026-07-14T00:00:00Z",
        updated_at="2026-07-14T00:00:00Z",
    )
    messages = [{"role": "user", "content": "Hello"}]

    updated = update_session_messages(session, messages)

    assert updated.id == "session-1"
    assert updated.title == "Chat"
    assert updated.messages == messages
    assert updated.created_at == "2026-07-14T00:00:00Z"
    assert updated.updated_at != "2026-07-14T00:00:00Z"


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
