# Simple AI Chat

A minimal AI chat app built with Streamlit and the OpenAI Python SDK. It uses an OpenAI-compatible Chat Completions API, defaults to DeepSeek, and can switch to OpenAI through environment variables.

## Features

- Local web chat UI
- Local multi-session management
- JSON session persistence under `.data/`
- Automatic titles for new chats
- Recent-first session sorting and title search
- JSON import/export for individual chats and all sessions
- Delete the last chat turn
- Streaming assistant responses
- Built-in prompt presets and custom system prompts
- Configurable DeepSeek / OpenAI provider
- Sidebar controls for `temperature` and `max_tokens`
- Markdown export for the current chat
- Streamlit Cloud deployment configuration
- Safe runtime diagnostics for local and Streamlit Cloud runs
- `.env` based API key, base URL, and model configuration
- Basic error messages without exposing secrets
- Unit tests for provider configuration, message construction, streaming helpers, and export formatting

## Quick Start

Run these commands in Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and fill in the API key for the provider you want to use.

Start the app:

```powershell
.\.venv\Scripts\streamlit.exe run app.py
```

Streamlit usually opens the browser automatically. If it does not, open the Local URL shown in the terminal, usually:

```text
http://localhost:8501
```

## DeepSeek Configuration

The project defaults to DeepSeek:

```env
AI_PROVIDER=deepseek

DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-pro
```

DeepSeek is compatible with the OpenAI Chat Completions API shape, but it requires a DeepSeek API key, base URL, and model name.

## OpenAI Configuration

To switch to OpenAI:

```env
AI_PROVIDER=openai

OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-5.6
```

## Environment Variables

| Variable | Description |
| --- | --- |
| `AI_PROVIDER` | Current provider. Supported values: `deepseek`, `openai` |
| `DEEPSEEK_API_KEY` | DeepSeek API key |
| `DEEPSEEK_BASE_URL` | DeepSeek API base URL. Default: `https://api.deepseek.com` |
| `DEEPSEEK_MODEL` | DeepSeek model name. Default: `deepseek-v4-pro` |
| `OPENAI_API_KEY` | OpenAI API key |
| `OPENAI_BASE_URL` | OpenAI API base URL. Default: `https://api.openai.com/v1` |
| `OPENAI_MODEL` | OpenAI model name. Default: `gpt-5.6` |

The sidebar shows whether the active provider API key is configured. It never displays the key value or a masked key fragment.

## Prompt Presets

The sidebar includes built-in prompt presets for common workflows:

- `General Assistant`
- `Translator`
- `Code Explainer`
- `Requirement Analyst`
- `Writing Polish`

The selected preset controls the system prompt sent with future model requests. You can also enable `Use custom system prompt` and enter a one-off custom instruction. Custom system prompts are local UI state in v1.6; they are not saved as named reusable presets and they are not stored in `.data/chats.json`.

## Generation Settings

The sidebar controls generation settings for the next user message:

| Setting | Default | Description |
| --- | --- | --- |
| `temperature` | `0.7` | Controls randomness. Lower is more stable; higher is more varied. |
| `max_tokens` | `1024` | Controls the maximum output length for one assistant response. |

Changing a setting affects the next request.

The app validates these settings in code as well as in the UI. `temperature` must be between `0.0` and `2.0`; `max_tokens` must be between `128` and `8192`.

## Export Conversation

When the current session has at least one message, the sidebar shows a `Download Markdown` button. It downloads the current browser session conversation as Markdown.

The export includes:

- Provider
- Model
- User messages
- Assistant replies

Markdown export is intended for readable sharing. JSON export in the Sessions sidebar is intended for backup and re-import.

## Local Sessions

The app stores local chat sessions in `.data/chats.json`. The `.data/` directory is ignored by Git so private chat history is not committed.

The sidebar supports:

- Creating a new chat
- Switching chats
- Searching chats by title
- Renaming the active chat
- Deleting the active chat
- Deleting the last turn from the active chat
- Exporting the active chat as JSON
- Exporting all local chats as JSON
- Importing chat sessions from JSON

New chats are automatically titled from the first user prompt unless the chat already has a custom title. The session list is sorted by most recently updated chat first.

Markdown export remains available for human-readable sharing. JSON export is intended for backup and re-import.

## Deployment

### Streamlit Cloud

1. Push this repository to GitHub.
2. Create a new app in Streamlit Cloud.
3. Select this repository and set the main file path to `app.py`.
4. Add secrets in Streamlit Cloud using the values from `.streamlit/secrets.toml.example`.
5. Set `AI_PROVIDER` to `deepseek` or `openai`.
6. Deploy the app.

Do not commit `.env` or `.streamlit/secrets.toml`. The repository includes `.streamlit/secrets.toml.example` only as a template.

### Streamlit Secrets Example

```toml
AI_PROVIDER = "deepseek"
DEEPSEEK_API_KEY = "your_deepseek_api_key"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-v4-pro"
```

## Project Structure

```text
.
|-- ai_chat/
|   |-- chat.py              # Chat Completions helpers and export formatting
|   |-- config.py            # Provider configuration parsing
|   |-- runtime.py           # Runtime environment detection
|   `-- sessions.py          # Local chat session storage helpers
|-- .streamlit/
|   |-- config.toml
|   `-- secrets.toml.example
|-- docs/
|   |-- design.md
|   |-- implementation-plan.md
|   `-- superpowers/
|-- tests/
|   |-- test_chat.py
|   |-- test_config.py
|   |-- test_runtime.py
|   `-- test_sessions.py
|-- .env.example
|-- .gitignore
|-- app.py                   # Streamlit app entry point
|-- README.md
`-- requirements.txt
```

## Run Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall app.py ai_chat
```

## Quality Checks

Run the same checks locally that CI runs on GitHub:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall app.py ai_chat
.\.venv\Scripts\python.exe -m ruff check .
```

The GitHub Actions workflow runs these checks on pushes and pull requests to `main`.

## Troubleshooting

### The page says the API key is missing

Make sure `.env.example` has been copied to `.env`, then fill in the API key for the selected provider.

For `AI_PROVIDER=deepseek`, set:

```env
DEEPSEEK_API_KEY=your_deepseek_api_key
```

For `AI_PROVIDER=openai`, set:

```env
OPENAI_API_KEY=your_openai_api_key
```

### Switch providers

Change `AI_PROVIDER` in `.env`, then restart Streamlit:

```env
AI_PROVIDER=openai
```

or:

```env
AI_PROVIDER=deepseek
```

### Model requests fail

Check these first:

- API key is valid
- Model name exists for the selected provider
- Base URL is correct
- Network can reach the selected provider

## GitHub

```text
https://github.com/cesuogaoshou/simple-ai-chat
```
