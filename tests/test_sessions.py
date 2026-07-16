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
    format_session_tags,
    import_sessions_json,
    list_session_tags,
    load_sessions,
    maybe_auto_title_session,
    normalize_session_tags,
    rename_session,
    save_sessions,
    search_sessions,
    session_to_dict,
    set_session_pinned,
    sort_sessions,
    sort_sessions_by_updated_at,
    update_session_messages,
    update_session_note,
    update_session_tags,
)


def test_create_default_session():
    session = create_default_session()

    assert session.title == "Untitled chat"
    assert session.messages == []
    assert session.id
    assert session.created_at
    assert session.updated_at


def test_create_default_session_is_unpinned():
    session = create_default_session()

    assert session.pinned is False
    assert session.tags == []
    assert session.note == ""


def test_create_session_uses_title():
    session = create_session("Project notes")

    assert session.title == "Project notes"
    assert session.messages == []


def test_create_session_falls_back_for_empty_title():
    session = create_session("")

    assert session.title == "Untitled chat"


def test_create_session_is_unpinned():
    session = create_session("Project notes")

    assert session.pinned is False
    assert session.tags == []
    assert session.note == ""


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


def test_export_session_json_round_trips():
    session = create_session("Exported")
    session.messages.append({"role": "assistant", "content": "Hi"})

    exported = export_session_json(session)
    imported = import_sessions_json(exported, existing_ids=set())

    assert len(imported) == 1
    assert imported[0].title == "Exported"
    assert imported[0].messages == [{"role": "assistant", "content": "Hi"}]


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


def test_import_sessions_json_rejects_invalid_shape():
    assert import_sessions_json('{"bad": true}', existing_ids=set()) == []


def test_import_sessions_json_generates_new_id_on_collision():
    session = create_session("Collision")
    imported = import_sessions_json(export_session_json(session), existing_ids={session.id})

    assert len(imported) == 1
    assert imported[0].id != session.id
