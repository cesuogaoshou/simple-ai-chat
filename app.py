from __future__ import annotations

from dotenv import load_dotenv
from openai import OpenAIError
import streamlit as st

from ai_chat.chat import (
    GenerationSettings,
    create_chat_client,
    export_messages_to_markdown,
    stream_chat_completion,
)
from ai_chat.config import ProviderConfig, get_provider_diagnostic, load_provider_config


def main() -> None:
    load_dotenv()
    st.set_page_config(page_title="Simple AI Chat", page_icon="chat")
    st.title("Simple AI Chat")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    config = load_config_for_ui()
    settings = render_sidebar(config)

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("Type a message...")
    if not prompt:
        return

    st.session_state.messages.append({"role": "user", "content": prompt})
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
            for chunk in stream_chat_completion(client, config, st.session_state.messages, settings):
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

    st.session_state.messages.append({"role": "assistant", "content": reply})


def load_config_for_ui() -> ProviderConfig | None:
    try:
        return load_provider_config()
    except ValueError as exc:
        st.warning(str(exc))
        return None


def render_sidebar(config: ProviderConfig | None) -> GenerationSettings:
    with st.sidebar:
        st.header("Configuration")
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
            st.session_state.messages = []
            st.rerun()

        if config is not None and st.session_state.get("messages"):
            st.download_button(
                "Download Markdown",
                data=export_messages_to_markdown(
                    st.session_state.messages,
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
