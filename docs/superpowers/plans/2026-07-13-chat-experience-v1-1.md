# Chat Experience v1.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add streaming responses, generation controls, Markdown export, and clean UI text to the existing Streamlit AI chat app.

**Architecture:** Keep the current boundaries: `app.py` owns Streamlit UI, `ai_chat/config.py` owns provider settings, and `ai_chat/chat.py` owns chat request helpers. Add testable chat helpers for generation settings, stream chunk extraction, streaming completion, and Markdown export.

**Tech Stack:** Python, Streamlit, OpenAI Python SDK, python-dotenv, pytest.

---

## File Structure

- Modify `ai_chat/chat.py`: fix readable system prompt text; add `GenerationSettings`, stream chunk extraction, streaming request generator, and Markdown export.
- Modify `app.py`: fix readable UI strings; add sidebar controls; render streamed assistant output; add Markdown download button.
- Modify `tests/test_chat.py`: add tests for settings, stream chunk extraction, streaming request arguments, and Markdown export.
- Modify `README.md`: document streaming, sidebar parameters, and conversation export.

## Task 1: Chat Helper Tests

**Files:**
- Modify: `tests/test_chat.py`
- Modify: `ai_chat/chat.py`

- [ ] **Step 1: Add failing tests for v1.1 chat helpers**

Append this to `tests/test_chat.py`:

```python
from types import SimpleNamespace

from ai_chat.chat import (
    GenerationSettings,
    export_messages_to_markdown,
    extract_stream_delta,
    stream_chat_completion,
)
from ai_chat.config import ProviderConfig


def test_generation_settings_defaults():
    settings = GenerationSettings()

    assert settings.temperature == 0.7
    assert settings.max_tokens == 1024


def test_extracts_delta_from_openai_compatible_stream_chunk():
    chunk = SimpleNamespace(
        choices=[
            SimpleNamespace(
                delta=SimpleNamespace(content="hello"),
            )
        ]
    )

    assert extract_stream_delta(chunk) == "hello"


def test_extract_stream_delta_returns_empty_string_for_missing_content():
    chunk = SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=None))])

    assert extract_stream_delta(chunk) == ""


def test_stream_chat_completion_passes_streaming_arguments():
    class FakeCompletions:
        def __init__(self):
            self.kwargs = None

        def create(self, **kwargs):
            self.kwargs = kwargs
            return [
                SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="Hi"))]),
                SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=" there"))]),
            ]

    fake_completions = FakeCompletions()
    fake_client = SimpleNamespace(chat=SimpleNamespace(completions=fake_completions))
    config = ProviderConfig(
        provider="deepseek",
        api_key="key",
        base_url="https://api.deepseek.com",
        model="deepseek-v4-pro",
    )

    chunks = list(
        stream_chat_completion(
            fake_client,
            config,
            [{"role": "user", "content": "Hello"}],
            GenerationSettings(temperature=0.2, max_tokens=256),
        )
    )

    assert chunks == ["Hi", " there"]
    assert fake_completions.kwargs["model"] == "deepseek-v4-pro"
    assert fake_completions.kwargs["stream"] is True
    assert fake_completions.kwargs["temperature"] == 0.2
    assert fake_completions.kwargs["max_tokens"] == 256


def test_exports_messages_to_markdown():
    markdown = export_messages_to_markdown(
        [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
        ],
        provider="deepseek",
        model="deepseek-v4-pro",
    )

    assert "# Simple AI Chat Export" in markdown
    assert "- Provider: deepseek" in markdown
    assert "- Model: deepseek-v4-pro" in markdown
    assert "## User" in markdown
    assert "Hello" in markdown
    assert "## Assistant" in markdown
    assert "Hi there" in markdown
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_chat.py -q
```

Expected: FAIL because `GenerationSettings`, `export_messages_to_markdown`, `extract_stream_delta`, and `stream_chat_completion` are not defined yet.

- [ ] **Step 3: Implement minimal chat helpers**

Update `ai_chat/chat.py` to this complete content:

```python
from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from openai import OpenAI

from ai_chat.config import ProviderConfig


SYSTEM_PROMPT = "You are a concise, accurate AI assistant. Reply in Chinese by default."
ALLOWED_ROLES = {"user", "assistant", "system"}


@dataclass(frozen=True)
class GenerationSettings:
    temperature: float = 0.7
    max_tokens: int = 1024


def build_chat_messages(history: Sequence[dict[str, str]]) -> list[dict[str, str]]:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for message in history:
        role = message.get("role", "")
        content = message.get("content", "")
        if role in ALLOWED_ROLES and content:
            messages.append({"role": role, "content": content})
    return messages


def create_chat_client(config: ProviderConfig) -> OpenAI:
    return OpenAI(api_key=config.api_key, base_url=config.base_url)


def request_chat_completion(client: OpenAI, config: ProviderConfig, history: Sequence[dict[str, str]]) -> str:
    response = client.chat.completions.create(
        model=config.model,
        messages=build_chat_messages(history),
    )
    message = response.choices[0].message.content
    return message or ""


def stream_chat_completion(
    client: OpenAI,
    config: ProviderConfig,
    history: Sequence[dict[str, str]],
    settings: GenerationSettings,
) -> Iterable[str]:
    stream = client.chat.completions.create(
        model=config.model,
        messages=build_chat_messages(history),
        temperature=settings.temperature,
        max_tokens=settings.max_tokens,
        stream=True,
    )
    for chunk in stream:
        delta = extract_stream_delta(chunk)
        if delta:
            yield delta


def extract_stream_delta(chunk: object) -> str:
    choices = getattr(chunk, "choices", [])
    if not choices:
        return ""
    delta = getattr(choices[0], "delta", None)
    if delta is None:
        return ""
    return getattr(delta, "content", None) or ""


def export_messages_to_markdown(
    messages: Sequence[dict[str, str]],
    *,
    provider: str,
    model: str,
) -> str:
    lines = [
        "# Simple AI Chat Export",
        "",
        f"- Provider: {provider}",
        f"- Model: {model}",
        "",
    ]
    for message in messages:
        role = message.get("role", "message").title()
        content = message.get("content", "")
        if not content:
            continue
        lines.extend([f"## {role}", "", content, ""])
    return "\n".join(lines).rstrip() + "\n"
```

- [ ] **Step 4: Run tests to verify pass**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_chat.py -q
```

Expected: PASS for all chat tests.

- [ ] **Step 5: Commit Task 1**

Run:

```powershell
git add ai_chat/chat.py tests/test_chat.py
git commit -m "feat: add chat streaming helpers"
```

## Task 2: Streamlit UI Integration

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Replace app UI with streaming and sidebar controls**

Update `app.py` to this complete content:

```python
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
from ai_chat.config import ProviderConfig, load_provider_config


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
```

- [ ] **Step 2: Run tests and compile check**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall app.py ai_chat
```

Expected: both commands exit 0.

- [ ] **Step 3: Commit Task 2**

Run:

```powershell
git add app.py
git commit -m "feat: add streaming chat ui controls"
```

## Task 3: README Update

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update README feature list**

In `README.md`, update the feature list under `## 你会得到什么` so it includes:

```markdown
- 流式回复，边生成边显示
- 侧边栏可调整 `temperature` 和 `max_tokens`
- 当前会话可导出为 Markdown
```

- [ ] **Step 2: Add a generation settings section**

Add this section before `## 运行测试`:

```markdown
## 生成参数

侧边栏支持调整本次会话后续请求的生成参数：

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `temperature` | `0.7` | 控制回复随机性，越低越稳定，越高越发散 |
| `max_tokens` | `1024` | 控制单次回复的最大输出长度 |

修改参数后，下一条用户消息会使用新的设置。
```

- [ ] **Step 3: Add export documentation**

Add this section before `## 常见问题`:

```markdown
## 导出对话

当当前会话里至少有一条消息时，侧边栏会显示 `Download Markdown` 按钮。点击后可以下载当前浏览器会话中的聊天记录。

导出文件包含：

- Provider
- 模型名
- 用户消息
- 助手回复

当前版本不保存历史记录；刷新页面或清空对话后，未下载的内容不会被持久化。
```

- [ ] **Step 4: Run verification**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall app.py ai_chat
```

Expected: both commands exit 0.

- [ ] **Step 5: Commit Task 3**

Run:

```powershell
git add README.md
git commit -m "docs: document chat experience v1.1"
```

## Task 4: Final Verification and Push

**Files:**
- No code changes unless verification reveals a defect.

- [ ] **Step 1: Run full verification**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall app.py ai_chat
git status --short
git log --oneline -5
```

Expected:

- `pytest`: all tests pass.
- `compileall`: exits 0.
- `git status --short`: empty.
- Recent commits include Task 1, Task 2, and Task 3 commits.

- [ ] **Step 2: Push to GitHub**

Run:

```powershell
git push
```

Expected: local `main` pushes to `origin/main`.

## Manual Acceptance

After implementation, run:

```powershell
.\.venv\Scripts\streamlit.exe run app.py
```

Verify:

- The app opens without Python errors.
- Missing API key still shows a configuration warning.
- With a valid API key, assistant text appears progressively.
- Changing `temperature` or `max_tokens` affects the next request payload.
- `Download Markdown` appears when messages exist and downloads readable Markdown.
