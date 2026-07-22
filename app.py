from __future__ import annotations

from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAIError

from ai_chat.chat import (
    GenerationSettings,
    create_chat_client,
    export_messages_to_markdown,
    stream_chat_completion,
)
from ai_chat.config import ProviderConfig, get_provider_diagnostic, load_provider_config
from ai_chat.preset_store import (
    create_custom_preset,
    custom_to_prompt_preset,
    delete_custom_preset,
    is_custom_preset_id,
    load_custom_presets,
    save_custom_presets,
)
from ai_chat.presets import (
    BUILT_IN_PRESETS,
    DEFAULT_PRESET_ID,
    get_preset,
    list_presets,
    resolve_system_prompt,
)
from ai_chat.runtime import detect_runtime
from ai_chat.sessions import (
    ChatSession,
    add_tag_to_sessions,
    create_session,
    delete_last_turn,
    delete_session,
    export_session_json,
    export_sessions_json,
    filter_visible_sessions,
    format_session_tags,
    import_sessions_json,
    list_session_tags,
    load_sessions,
    maybe_auto_title_session,
    normalize_session_tags,
    remove_tag_from_sessions,
    rename_session,
    save_sessions,
    set_session_pinned,
    sort_sessions,
    update_session_messages,
    update_session_note,
    update_session_tags,
)

SESSION_STORE = Path(".data/chats.json")
PRESET_STORE = Path(".data/presets.json")


def main() -> None:
    load_dotenv()
    st.set_page_config(page_title="Simple AI Chat", page_icon="chat")
    st.title("Simple AI Chat")

    if "sessions" not in st.session_state:
        st.session_state.sessions = sort_sessions(load_sessions(SESSION_STORE))
        st.session_state.active_session_id = st.session_state.sessions[0].id

    if "preset_id" not in st.session_state:
        st.session_state.preset_id = DEFAULT_PRESET_ID
    if "use_custom_system_prompt" not in st.session_state:
        st.session_state.use_custom_system_prompt = False
    if "custom_system_prompt" not in st.session_state:
        st.session_state.custom_system_prompt = ""
    if "custom_presets" not in st.session_state:
        reserved_ids = {preset.id for preset in BUILT_IN_PRESETS}
        st.session_state.custom_presets = load_custom_presets(
            PRESET_STORE,
            reserved_ids=reserved_ids,
        )
    if "custom_preset_name" not in st.session_state:
        st.session_state.custom_preset_name = ""
    if "session_search_query" not in st.session_state:
        st.session_state.session_search_query = ""
    if "session_tag_filter" not in st.session_state:
        st.session_state.session_tag_filter = "All tags"
    if "session_batch_tag" not in st.session_state:
        st.session_state.session_batch_tag = ""
    if "confirm_delete_active_chat" not in st.session_state:
        st.session_state.confirm_delete_active_chat = False

    config = load_config_for_ui()
    settings = render_sidebar(config)
    system_prompt = active_system_prompt()
    session = active_session()

    for message in session.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("Type a message...")
    if not prompt:
        return

    messages = [*session.messages, {"role": "user", "content": prompt}]
    session = maybe_auto_title_session(update_session_messages(session, messages), prompt)
    replace_active_session(session)
    with st.chat_message("user"):
        st.markdown(prompt)

    if config is None:
        with st.chat_message("assistant"):
            st.error("Please complete .env configuration before sending a message.")
        return

    reply = ""
    with st.chat_message("assistant"):
        placeholder = st.empty()
        try:
            client = create_chat_client(config)
            for chunk in stream_chat_completion(
                client,
                config,
                session.messages,
                settings,
                system_prompt=system_prompt,
            ):
                reply += chunk
                placeholder.markdown(reply)
        except OpenAIError as exc:
            error_text = f"Model request failed: {exc.__class__.__name__}. Check API key, model, or network."
            reply = append_error_note(reply, error_text)
            placeholder.error(reply)
        except Exception as exc:
            error_text = f"Request failed: {exc}"
            reply = append_error_note(reply, error_text)
            placeholder.error(reply)
        else:
            if not reply:
                reply = "No response content was returned."
                placeholder.warning(reply)

    messages = [*session.messages, {"role": "assistant", "content": reply}]
    replace_active_session(update_session_messages(session, messages))


def load_config_for_ui() -> ProviderConfig | None:
    try:
        return load_provider_config()
    except ValueError as exc:
        st.warning(str(exc))
        return None


def active_session() -> ChatSession:
    for session in st.session_state.sessions:
        if session.id == st.session_state.active_session_id:
            return session
    st.session_state.active_session_id = st.session_state.sessions[0].id
    return st.session_state.sessions[0]


def replace_active_session(updated: ChatSession) -> None:
    st.session_state.sessions = sort_sessions(
        [
            updated if session.id == updated.id else session
            for session in st.session_state.sessions
        ]
    )
    save_sessions(SESSION_STORE, st.session_state.sessions)


def render_sessions_sidebar() -> None:
    st.header("Sessions")
    current = active_session()
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
    visible_ids = [session.id for session in visible_sessions]
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

    current = active_session()
    new_title = st.text_input("Chat title", value=current.title)
    if new_title != current.title:
        replace_active_session(rename_session(current, new_title))

    pin_label = "Unpin chat" if current.pinned else "Pin chat"
    if st.button(pin_label, use_container_width=True):
        replace_active_session(set_session_pinned(current, not current.pinned))
        st.rerun()

    tag_text = st.text_input("Chat tags", value=format_session_tags(current.tags))
    updated_tags = normalize_session_tags(tag_text)
    if updated_tags != current.tags:
        replace_active_session(update_session_tags(current, updated_tags))
        st.rerun()

    note = st.text_area("Chat note", value=current.note)
    if note.strip() != current.note:
        replace_active_session(update_session_note(current, note))
        st.rerun()

    if st.button("New chat", use_container_width=True):
        session = create_session("Untitled chat")
        st.session_state.sessions.append(session)
        st.session_state.active_session_id = session.id
        st.session_state.sessions = sort_sessions(st.session_state.sessions)
        save_sessions(SESSION_STORE, st.session_state.sessions)
        st.rerun()

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

    current = active_session()
    st.download_button(
        "Export JSON",
        data=export_session_json(current),
        file_name=f"{current.title or 'chat'}.json",
        mime="application/json",
        use_container_width=True,
    )
    st.download_button(
        "Export All JSON",
        data=export_sessions_json(st.session_state.sessions),
        file_name="simple-ai-chat-sessions.json",
        mime="application/json",
        use_container_width=True,
    )
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

    uploaded = st.file_uploader("Import JSON", type=["json"])
    if uploaded is not None:
        imported = import_sessions_json(
            uploaded.getvalue().decode("utf-8"),
            existing_ids={session.id for session in st.session_state.sessions},
        )
        if imported:
            st.session_state.sessions.extend(imported)
            st.session_state.active_session_id = imported[0].id
            st.session_state.sessions = sort_sessions(st.session_state.sessions)
            save_sessions(SESSION_STORE, st.session_state.sessions)
            st.success(f"Imported {len(imported)} session(s).")
            st.rerun()
        else:
            st.error("Invalid chat session JSON.")


def session_title_for_id(session_id: str) -> str:
    for session in st.session_state.sessions:
        if session.id == session_id:
            return session.title
    return "Untitled chat"


def runtime_custom_presets():
    return [
        custom_to_prompt_preset(preset)
        for preset in st.session_state.custom_presets
    ]


def active_system_prompt() -> str:
    custom_prompt = (
        st.session_state.custom_system_prompt
        if st.session_state.use_custom_system_prompt
        else ""
    )
    return resolve_system_prompt(
        st.session_state.preset_id,
        custom_prompt,
        custom_presets=runtime_custom_presets(),
    )


def render_prompt_preset_sidebar() -> None:
    st.subheader("Prompt Preset")
    custom_presets = runtime_custom_presets()
    presets = list_presets(custom_presets)
    preset_ids = [preset.id for preset in presets]
    selected_id = st.selectbox(
        "Preset",
        options=preset_ids,
        index=(
            preset_ids.index(st.session_state.preset_id)
            if st.session_state.preset_id in preset_ids
            else 0
        ),
        format_func=lambda preset_id: get_preset(preset_id, custom_presets).name,
    )
    st.session_state.preset_id = selected_id
    st.caption(get_preset(selected_id, custom_presets).description)
    st.checkbox("Use custom system prompt", key="use_custom_system_prompt")
    if st.session_state.use_custom_system_prompt:
        st.text_area(
            "Custom system prompt",
            key="custom_system_prompt",
            height=120,
        )
        st.text_input("Custom preset name", key="custom_preset_name")
        if st.button("Save as preset", use_container_width=True):
            existing_ids = {preset.id for preset in BUILT_IN_PRESETS}
            existing_ids.update(preset.id for preset in st.session_state.custom_presets)
            preset = create_custom_preset(
                st.session_state.custom_preset_name,
                st.session_state.custom_system_prompt,
                existing_ids,
            )
            if preset is None:
                st.warning("Enter a custom system prompt before saving a preset.")
            else:
                st.session_state.custom_presets.append(preset)
                save_custom_presets(PRESET_STORE, st.session_state.custom_presets)
                st.session_state.preset_id = preset.id
                st.session_state.use_custom_system_prompt = False
                st.session_state.custom_system_prompt = ""
                st.session_state.custom_preset_name = ""
                st.rerun()

    if is_custom_preset_id(selected_id):
        if st.button("Delete custom preset", use_container_width=True):
            st.session_state.custom_presets = delete_custom_preset(
                st.session_state.custom_presets,
                selected_id,
            )
            save_custom_presets(PRESET_STORE, st.session_state.custom_presets)
            st.session_state.preset_id = DEFAULT_PRESET_ID
            st.rerun()


def render_sidebar(config: ProviderConfig | None) -> GenerationSettings:
    with st.sidebar:
        render_sessions_sidebar()

        st.divider()
        st.header("Configuration")
        st.caption(detect_runtime().label)
        if config is None:
            st.caption("Current configuration is unavailable.")
        else:
            st.write(f"Provider: `{config.provider}`")
            st.write(f"Model: `{config.model}`")
            st.write(f"Base URL: `{config.base_url}`")

        diagnostic = get_provider_diagnostic()
        if diagnostic.has_api_key:
            st.success(diagnostic.status_text)
        else:
            st.warning(diagnostic.status_text)

        st.divider()
        st.subheader("Generation")
        temperature = st.slider("Temperature", min_value=0.0, max_value=2.0, value=0.7, step=0.1)
        max_tokens = st.number_input("Max tokens", min_value=128, max_value=8192, value=1024, step=128)

        st.divider()
        render_prompt_preset_sidebar()

        st.divider()
        if st.button("Clear chat", use_container_width=True):
            replace_active_session(update_session_messages(active_session(), []))
            st.rerun()

        if active_session().messages and st.button("Delete last turn", use_container_width=True):
            replace_active_session(delete_last_turn(active_session()))
            st.rerun()

        if config is not None and active_session().messages:
            st.download_button(
                "Download Markdown",
                data=export_messages_to_markdown(
                    active_session().messages,
                    provider=config.provider,
                    model=config.model,
                ),
                file_name="simple-ai-chat-export.md",
                mime="text/markdown",
                use_container_width=True,
            )

    return GenerationSettings(temperature=temperature, max_tokens=int(max_tokens))


def append_error_note(partial_reply: str, error_text: str) -> str:
    if partial_reply:
        return f"{partial_reply}\n\n> {error_text}"
    return error_text


if __name__ == "__main__":
    main()
