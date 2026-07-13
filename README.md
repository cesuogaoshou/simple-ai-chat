# Simple AI Chat

A minimal AI chat app built with Streamlit and the OpenAI Python SDK. It uses an OpenAI-compatible Chat Completions API, defaults to DeepSeek, and can switch to OpenAI through environment variables.

## Features

- Local web chat UI
- Session-only conversation context
- Streaming assistant responses
- Configurable DeepSeek / OpenAI provider
- Sidebar controls for `temperature` and `max_tokens`
- Markdown export for the current conversation
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

## Generation Settings

The sidebar controls generation settings for the next user message:

| Setting | Default | Description |
| --- | --- | --- |
| `temperature` | `0.7` | Controls randomness. Lower is more stable; higher is more varied. |
| `max_tokens` | `1024` | Controls the maximum output length for one assistant response. |

Changing a setting affects the next request.

## Export Conversation

When the current session has at least one message, the sidebar shows a `Download Markdown` button. It downloads the current browser session conversation as Markdown.

The export includes:

- Provider
- Model
- User messages
- Assistant replies

The app does not persist history. If you refresh the page or clear the chat before downloading, the unsaved conversation is gone.

## Project Structure

```text
.
├── ai_chat/
│   ├── chat.py              # Chat Completions helpers and export formatting
│   └── config.py            # Provider configuration parsing
├── docs/
│   ├── design.md
│   ├── implementation-plan.md
│   └── superpowers/
├── tests/
│   ├── test_chat.py
│   └── test_config.py
├── .env.example
├── .gitignore
├── app.py                   # Streamlit app entry point
├── README.md
└── requirements.txt
```

## Run Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall app.py ai_chat
```

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
