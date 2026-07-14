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
from ai_chat.runtime import detect_runtime
from ai_chat.sessions import (
    ChatSession,
    create_session,
    delete_session,
    load_sessions,
    rename_session,
    save_sessions,
    update_session_messages,
)

SESSION_STORE = Path(".data/chats.json")


def main() -> None:
    load_dotenv()
    st.set_page_config(page_title="Simple AI Chat", page_icon="chat")
    st.title("Simple AI Chat")

    if "sessions" not in st.session_state:
        st.session_state.sessions = load_sessions(SESSION_STORE)
        st.session_state.active_session_id = st.session_state.sessions[0].id

    config = load_config_for_ui()
    settings = render_sidebar(config)
    session = active_session()

    for message in session.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("Type a message...")
    if not prompt:
        return

    messages = [*session.messages, {"role": "user", "content": prompt}]
    session = update_session_messages(session, messages)
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
            for chunk in stream_chat_completion(client, config, session.messages, settings):
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
    st.session_state.sessions = [
        updated if session.id == updated.id else session
        for session in st.session_state.sessions
    ]
    save_sessions(SESSION_STORE, st.session_state.sessions)


def render_sessions_sidebar() -> None:
    st.header("Sessions")
    current = active_session()
    session_ids = [session.id for session in st.session_state.sessions]
    selected_id = st.selectbox(
        "Active chat",
        options=session_ids,
        index=session_ids.index(current.id),
        format_func=session_title_for_id,
    )
    st.session_state.active_session_id = selected_id

    current = active_session()
    new_title = st.text_input("Chat title", value=current.title)
    if new_title != current.title:
        replace_active_session(rename_session(current, new_title))

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


def session_title_for_id(session_id: str) -> str:
    for session in st.session_state.sessions:
        if session.id == session_id:
            return session.title
    return "Untitled chat"


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
        if st.button("Clear chat", use_container_width=True):
            replace_active_session(update_session_messages(active_session(), []))
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
