from __future__ import annotations

from dotenv import load_dotenv
from openai import OpenAIError
import streamlit as st

from ai_chat.chat import create_chat_client, request_chat_completion
from ai_chat.config import ProviderConfig, load_provider_config


def main() -> None:
    load_dotenv()
    st.set_page_config(page_title="Simple AI Chat", page_icon="💬")
    st.title("Simple AI Chat")

    config = load_config_for_ui()
    render_sidebar(config)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("输入消息...")
    if not prompt:
        return

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    if config is None:
        with st.chat_message("assistant"):
            st.error("请先完成 .env 配置后再发送消息。")
        return

    with st.chat_message("assistant"):
        with st.spinner("正在生成回复..."):
            try:
                client = create_chat_client(config)
                reply = request_chat_completion(client, config, st.session_state.messages)
            except OpenAIError as exc:
                reply = f"模型请求失败：{exc.__class__.__name__}。请检查 API Key、模型名或网络连接。"
                st.error(reply)
            except Exception as exc:
                reply = f"请求失败：{exc}"
                st.error(reply)
            else:
                st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})


def load_config_for_ui() -> ProviderConfig | None:
    try:
        return load_provider_config()
    except ValueError as exc:
        st.warning(str(exc))
        return None


def render_sidebar(config: ProviderConfig | None) -> None:
    with st.sidebar:
        st.header("配置")
        if config is None:
            st.caption("当前配置不可用")
        else:
            st.write(f"Provider: `{config.provider}`")
            st.write(f"Model: `{config.model}`")
            st.write(f"Base URL: `{config.base_url}`")

        if st.button("清空对话", use_container_width=True):
            st.session_state.messages = []
            st.rerun()


if __name__ == "__main__":
    main()
