# Chat Experience v1.1 Design

## Summary

v1.1 focuses on improving the existing simple chat experience without changing the project architecture. The app will keep the current Streamlit + OpenAI-compatible Chat Completions design, and add streaming responses, adjustable generation parameters, and Markdown export for the current session.

## Goals

- Show assistant responses progressively while the model generates text.
- Let users adjust `temperature` and `max_tokens` from the sidebar.
- Let users download the current conversation as a Markdown file.
- Keep DeepSeek and OpenAI on the same OpenAI-compatible Chat Completions path.
- Preserve the current no-database, session-only behavior.

## Non-Goals

- No login or multi-user support.
- No persistent chat history.
- No RAG, file upload, vector database, or tool calling.
- No deployment automation.
- No switch from Streamlit to another frontend framework.

## User Experience

The sidebar will show the current Provider, model, Base URL, and two controls:

- `temperature`: numeric slider from `0.0` to `2.0`, default `0.7`, step `0.1`.
- `max_tokens`: numeric input from `128` to `8192`, default `1024`, step `128`.

The main chat area remains the first screen. When the user sends a message, the assistant reply appears progressively in the assistant chat bubble. If the request fails, the app shows a concise error and does not expose API keys.

If there is at least one message in the session, the sidebar shows a download button for the current conversation as Markdown. The exported Markdown includes a title, provider/model metadata, and messages grouped by role.

## Architecture

The existing module boundaries remain:

- `app.py`: Streamlit UI, sidebar controls, streaming display, download button.
- `ai_chat/config.py`: Provider configuration only.
- `ai_chat/chat.py`: message construction, streaming request logic, Markdown export formatting.

v1.1 adds a small generation settings object in `ai_chat/chat.py` or a focused helper module if tests show the file is becoming unclear. The settings will carry `temperature` and `max_tokens` from the UI to the model request.

## Data Flow

1. Streamlit loads Provider config from `.env`.
2. Sidebar reads generation settings from user controls.
3. User sends a message.
4. The app appends the user message to `st.session_state.messages`.
5. The chat module builds OpenAI-compatible messages with the existing system prompt.
6. The SDK request uses `stream=True`, `temperature`, and `max_tokens`.
7. The app progressively writes chunks into the assistant message container.
8. The final assistant text is appended to session history.
9. The export button formats `st.session_state.messages` into Markdown when clicked.

## Error Handling

- Missing or invalid Provider config keeps the current blocking behavior.
- Streaming errors show a concise message in the assistant bubble.
- If a stream fails after partial text has appeared, the final saved assistant message will include the partial text plus an error note, so the UI matches session history.
- Empty conversations do not show the download button.

## Testing

Unit tests will cover:

- Generation settings default values.
- Streaming chunk extraction from OpenAI-compatible response events.
- Passing `temperature`, `max_tokens`, and `stream=True` into the Chat Completions call.
- Markdown export format for user and assistant messages.
- Empty-message export returns a minimal but valid Markdown document or disables export at the UI layer.

Manual verification will cover:

- Streamlit starts with `streamlit run app.py`.
- Missing API key still shows a clear configuration warning.
- A real provider request streams text into the assistant bubble.
- Sidebar parameter changes affect subsequent requests.
- Downloaded Markdown includes the visible conversation.

## Acceptance Criteria

- Existing tests still pass.
- New unit tests pass.
- `python -m compileall app.py ai_chat` succeeds.
- README documents streaming, parameters, and export.
- Current GitHub remote remains `origin/main`.
- No `.env`, virtual environment, cache, or secret file is committed.
