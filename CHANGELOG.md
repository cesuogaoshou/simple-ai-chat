# Changelog

## v1.8 - Conversation Library

- Added pinned local chat sessions.
- Added title and message-content session search.
- Preserved pinned state in chat JSON import and export.
- Kept old chat JSON compatible by defaulting missing pinned state to unpinned.

## v1.7 - Custom Prompt Presets

- Added local saved custom prompt presets.
- Added custom preset save and delete controls.
- Kept custom presets separate from chat session JSON.
- Documented local custom preset storage.

## v1.6 - Prompt Presets

- Added built-in prompt presets.
- Added optional custom system prompts.
- Added system prompt support to chat request construction.
- Documented preset behavior and limitations.

## v1.5 - Conversation UX

- Added automatic titles for new chats.
- Added recent-first session sorting and title search.
- Added all-session JSON export.
- Added last-turn deletion for the active chat.

## v1.4 - Local Session Management

- Added local multi-session management.
- Added JSON persistence under `.data/chats.json`.
- Added JSON import and export for sessions.
- Kept Markdown export for readable sharing.

## v1.3 - Deployment Readiness

- Added Streamlit deployment configuration.
- Added Streamlit secrets template.
- Added safe runtime diagnostics.
- Added Streamlit Cloud deployment documentation.

## v1.2 - Engineering Quality

- Added safe provider diagnostics in the Streamlit sidebar.
- Added validation for generation settings.
- Added Ruff linting.
- Added GitHub Actions CI.
- Updated project maintenance documentation.

## v1.1 - Chat Experience

- Added streaming assistant responses.
- Added sidebar controls for `temperature` and `max_tokens`.
- Added Markdown export for the current conversation.
- Reworked README content for stable cross-platform rendering.

## v1.0 - Initial Chat

- Added Streamlit chat UI.
- Added configurable DeepSeek and OpenAI providers.
- Added session-only chat history.
- Added basic tests and project documentation.
