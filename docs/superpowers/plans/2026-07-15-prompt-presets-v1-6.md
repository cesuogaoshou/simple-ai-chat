# Prompt Presets v1.6 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add built-in prompt presets and optional custom system prompts so users can switch assistant behavior before sending messages.

**Architecture:** Add a pure `ai_chat.presets` module for preset definitions and prompt resolution. Extend `ai_chat.chat` to accept an optional system prompt while preserving existing defaults, then wire preset controls into the Streamlit sidebar without changing session JSON shape.

**Tech Stack:** Python, Streamlit, pytest, Ruff, OpenAI-compatible Chat Completions.

---

## File Structure

- Create `ai_chat/presets.py`: prompt preset dataclass, built-in catalog, lookup, list, and resolution helpers.
- Create `tests/test_presets.py`: unit tests for preset catalog and system prompt resolution.
- Modify `ai_chat/chat.py`: allow custom system prompt injection into Chat Completions messages.
- Modify `tests/test_chat.py`: verify custom system prompt behavior and compatibility.
- Modify `app.py`: render prompt preset controls and pass resolved prompt into streaming requests.
- Modify `README.md`: document built-in prompt presets and custom system prompt behavior.
- Modify `CHANGELOG.md`: add v1.6 release notes.

Use `.\.venv\Scripts\python.exe -m pytest -q --basetemp .pytest_cache/tmp` for test runs in this workspace because the default Windows temp directory can raise permission errors.

## Task 1: Preset Domain Module

**Files:**
- Create: `ai_chat/presets.py`
- Create: `tests/test_presets.py`

- [ ] **Step 1: Write failing preset tests**

Create `tests/test_presets.py`:

```python
from ai_chat.presets import (
    DEFAULT_PRESET_ID,
    BUILT_IN_PRESETS,
    get_preset,
    list_presets,
    resolve_system_prompt,
)


def test_built_in_presets_include_default():
    preset_ids = {preset.id for preset in BUILT_IN_PRESETS}

    assert DEFAULT_PRESET_ID == "general"
    assert DEFAULT_PRESET_ID in preset_ids


def test_list_presets_returns_built_in_presets():
    assert list_presets() == list(BUILT_IN_PRESETS)


def test_get_preset_returns_requested_preset():
    preset = get_preset("translator")

    assert preset.id == "translator"
    assert preset.name == "Translator"
    assert "translate" in preset.system_prompt.casefold()


def test_get_preset_falls_back_for_unknown_id():
    assert get_preset("missing") == get_preset(DEFAULT_PRESET_ID)


def test_resolve_system_prompt_prefers_non_empty_custom_prompt():
    assert resolve_system_prompt("general", "  Custom prompt  ") == "Custom prompt"


def test_resolve_system_prompt_falls_back_for_blank_custom_prompt():
    assert resolve_system_prompt("translator", "   ") == get_preset("translator").system_prompt
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_presets.py -q --basetemp .pytest_cache/tmp
```

Expected: FAIL with `ModuleNotFoundError: No module named 'ai_chat.presets'`.

- [ ] **Step 3: Implement preset module**

Create `ai_chat/presets.py`:

```python
from __future__ import annotations

from dataclasses import dataclass


DEFAULT_PRESET_ID = "general"


@dataclass(frozen=True)
class PromptPreset:
    id: str
    name: str
    description: str
    system_prompt: str


BUILT_IN_PRESETS = (
    PromptPreset(
        id="general",
        name="General Assistant",
        description="Concise, accurate help in Chinese by default.",
        system_prompt="You are a concise, accurate AI assistant. Reply in Chinese by default.",
    ),
    PromptPreset(
        id="translator",
        name="Translator",
        description="Translate between Chinese and English with polished wording.",
        system_prompt=(
            "You are a professional translator. Translate the user's text into polished "
            "Chinese when the source is English, and into polished English when the source "
            "is Chinese. Preserve meaning and avoid adding unrelated commentary."
        ),
    ),
    PromptPreset(
        id="code_explainer",
        name="Code Explainer",
        description="Explain code clearly with assumptions, risks, and examples.",
        system_prompt=(
            "You explain code clearly and pragmatically. Identify assumptions, important "
            "control flow, edge cases, and risks. Use concise examples when helpful."
        ),
    ),
    PromptPreset(
        id="requirement_analyst",
        name="Requirement Analyst",
        description="Turn rough ideas into structured requirements and tasks.",
        system_prompt=(
            "You are a requirements analyst. Turn rough ideas into clear goals, constraints, "
            "user stories, edge cases, and implementation tasks. Ask concise questions only "
            "when needed."
        ),
    ),
    PromptPreset(
        id="writing_polish",
        name="Writing Polish",
        description="Improve clarity, structure, and tone while preserving meaning.",
        system_prompt=(
            "You improve writing while preserving the original meaning. Make structure, "
            "wording, and tone clearer. Explain notable changes briefly when useful."
        ),
    ),
)


def list_presets() -> list[PromptPreset]:
    return list(BUILT_IN_PRESETS)


def get_preset(preset_id: str) -> PromptPreset:
    for preset in BUILT_IN_PRESETS:
        if preset.id == preset_id:
            return preset
    return BUILT_IN_PRESETS[0]


def resolve_system_prompt(preset_id: str, custom_prompt: str = "") -> str:
    cleaned = custom_prompt.strip()
    if cleaned:
        return cleaned
    return get_preset(preset_id).system_prompt
```

- [ ] **Step 4: Verify preset tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_presets.py -q --basetemp .pytest_cache/tmp
.\.venv\Scripts\python.exe -m ruff check .
```

Expected:

- `tests/test_presets.py`: all tests pass.
- Ruff exits 0.

- [ ] **Step 5: Commit Task 1**

Run:

```powershell
git add ai_chat/presets.py tests/test_presets.py
git commit -m "feat: add prompt preset catalog"
```

## Task 2: Chat System Prompt Injection

**Files:**
- Modify: `ai_chat/chat.py`
- Modify: `tests/test_chat.py`

- [ ] **Step 1: Add failing chat prompt tests**

Add these tests after `test_builds_chat_completion_messages_with_system_prompt` in `tests/test_chat.py`:

```python
def test_build_chat_messages_uses_custom_system_prompt():
    messages = build_chat_messages(
        [{"role": "user", "content": "Hello"}],
        system_prompt="Custom system prompt",
    )

    assert messages[0] == {"role": "system", "content": "Custom system prompt"}
    assert messages[1] == {"role": "user", "content": "Hello"}


def test_build_chat_messages_falls_back_for_blank_system_prompt():
    messages = build_chat_messages(
        [{"role": "user", "content": "Hello"}],
        system_prompt="   ",
    )

    assert messages[0] == {"role": "system", "content": SYSTEM_PROMPT}
```

Add this test after `test_build_chat_completion_kwargs_adds_deepseek_thinking_disabled`:

```python
def test_build_chat_completion_kwargs_uses_custom_system_prompt():
    config = ProviderConfig(
        provider="deepseek",
        api_key="key",
        base_url="https://api.deepseek.com",
        model="deepseek-v4-pro",
    )

    kwargs = build_chat_completion_kwargs(
        config,
        [{"role": "user", "content": "Hello"}],
        GenerationSettings(),
        system_prompt="Custom prompt",
    )

    assert kwargs["messages"][0] == {"role": "system", "content": "Custom prompt"}
```

Add this assertion to `test_stream_chat_completion_passes_streaming_arguments` after `assert fake_completions.kwargs["max_tokens"] == 256`:

```python
    assert fake_completions.kwargs["messages"][0] == {
        "role": "system",
        "content": SYSTEM_PROMPT,
    }
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_chat.py -q --basetemp .pytest_cache/tmp
```

Expected: FAIL because `build_chat_messages` and `build_chat_completion_kwargs` do not accept `system_prompt`.

- [ ] **Step 3: Update chat helper signatures**

In `ai_chat/chat.py`, replace `build_chat_messages` with:

```python
def build_chat_messages(
    history: Sequence[dict[str, str]], system_prompt: str | None = None
) -> list[dict[str, str]]:
    prompt = system_prompt.strip() if system_prompt else SYSTEM_PROMPT
    if not prompt:
        prompt = SYSTEM_PROMPT
    messages = [{"role": "system", "content": prompt}]
    for message in history:
        role = message.get("role", "")
        content = message.get("content", "")
        if role in ALLOWED_ROLES and content:
            messages.append({"role": role, "content": content})
    return messages
```

Replace `request_chat_completion` with:

```python
def request_chat_completion(
    client: OpenAI,
    config: ProviderConfig,
    history: Sequence[dict[str, str]],
    system_prompt: str | None = None,
) -> str:
    response = client.chat.completions.create(
        **build_chat_completion_kwargs(config, history, system_prompt=system_prompt)
    )
    message = response.choices[0].message.content
    return message or ""
```

Replace the `build_chat_completion_kwargs` signature and `messages` line with:

```python
def build_chat_completion_kwargs(
    config: ProviderConfig,
    history: Sequence[dict[str, str]],
    settings: GenerationSettings | None = None,
    *,
    stream: bool = False,
    system_prompt: str | None = None,
) -> dict[str, object]:
    kwargs: dict[str, object] = {
        "model": config.model,
        "messages": build_chat_messages(history, system_prompt),
    }
```

Replace `stream_chat_completion` with:

```python
def stream_chat_completion(
    client: OpenAI,
    config: ProviderConfig,
    history: Sequence[dict[str, str]],
    settings: GenerationSettings,
    system_prompt: str | None = None,
) -> Iterable[str]:
    stream = client.chat.completions.create(
        **build_chat_completion_kwargs(
            config,
            history,
            settings,
            stream=True,
            system_prompt=system_prompt,
        )
    )
    for chunk in stream:
        delta = extract_stream_delta(chunk)
        if delta:
            yield delta
```

- [ ] **Step 4: Verify chat tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_chat.py -q --basetemp .pytest_cache/tmp
.\.venv\Scripts\python.exe -m ruff check .
```

Expected:

- `tests/test_chat.py`: all tests pass.
- Ruff exits 0.

- [ ] **Step 5: Commit Task 2**

Run:

```powershell
git add ai_chat/chat.py tests/test_chat.py
git commit -m "feat: allow custom chat system prompts"
```

## Task 3: Streamlit Preset Sidebar

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Update imports**

Add this import in `app.py`:

```python
from ai_chat.presets import DEFAULT_PRESET_ID, get_preset, list_presets, resolve_system_prompt
```

- [ ] **Step 2: Add preset state initialization**

In `main()`, after session initialization, add:

```python
    if "preset_id" not in st.session_state:
        st.session_state.preset_id = DEFAULT_PRESET_ID
    if "use_custom_system_prompt" not in st.session_state:
        st.session_state.use_custom_system_prompt = False
    if "custom_system_prompt" not in st.session_state:
        st.session_state.custom_system_prompt = ""
```

- [ ] **Step 3: Pass resolved system prompt to streaming**

In `main()`, after `settings = render_sidebar(config)`, add:

```python
    system_prompt = active_system_prompt()
```

In the `stream_chat_completion` call, replace:

```python
            for chunk in stream_chat_completion(client, config, session.messages, settings):
```

with:

```python
            for chunk in stream_chat_completion(
                client,
                config,
                session.messages,
                settings,
                system_prompt=system_prompt,
            ):
```

- [ ] **Step 4: Add preset helper functions**

Add these functions above `render_sidebar` in `app.py`:

```python
def active_system_prompt() -> str:
    custom_prompt = (
        st.session_state.custom_system_prompt
        if st.session_state.use_custom_system_prompt
        else ""
    )
    return resolve_system_prompt(st.session_state.preset_id, custom_prompt)


def render_prompt_preset_sidebar() -> None:
    st.subheader("Prompt Preset")
    presets = list_presets()
    preset_ids = [preset.id for preset in presets]
    selected_id = st.selectbox(
        "Preset",
        options=preset_ids,
        index=preset_ids.index(st.session_state.preset_id)
        if st.session_state.preset_id in preset_ids
        else 0,
        format_func=lambda preset_id: get_preset(preset_id).name,
    )
    st.session_state.preset_id = selected_id
    st.caption(get_preset(selected_id).description)
    st.checkbox("Use custom system prompt", key="use_custom_system_prompt")
    if st.session_state.use_custom_system_prompt:
        st.text_area(
            "Custom system prompt",
            key="custom_system_prompt",
            height=120,
        )
```

- [ ] **Step 5: Render preset sidebar section**

In `render_sidebar()`, after the generation settings controls and before the divider that contains `Clear chat`, add:

```python
        st.divider()
        render_prompt_preset_sidebar()
```

- [ ] **Step 6: Run verification**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp .pytest_cache/tmp
.\.venv\Scripts\python.exe -m compileall app.py ai_chat
.\.venv\Scripts\python.exe -m ruff check .
```

Expected:

- pytest exits 0.
- compileall exits 0.
- Ruff exits 0.

- [ ] **Step 7: Commit Task 3**

Run:

```powershell
git add app.py
git commit -m "feat: add prompt preset sidebar"
```

## Task 4: Documentation and Final Verification

**Files:**
- Modify: `README.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Update README feature list**

In `README.md`, add this bullet near the chat feature bullets:

```markdown
- Built-in prompt presets and custom system prompts
```

- [ ] **Step 2: Add README prompt presets section**

Add this section before `## Generation Settings`:

```markdown
## Prompt Presets

The sidebar includes built-in prompt presets for common workflows:

- `General Assistant`
- `Translator`
- `Code Explainer`
- `Requirement Analyst`
- `Writing Polish`

The selected preset controls the system prompt sent with future model requests. You can also enable `Use custom system prompt` and enter a one-off custom instruction. Custom system prompts are local UI state in v1.6; they are not saved as named reusable presets and they are not stored in `.data/chats.json`.
```

- [ ] **Step 3: Update CHANGELOG**

Add this entry immediately after `# Changelog`:

```markdown
## v1.6 - Prompt Presets

- Added built-in prompt presets.
- Added optional custom system prompts.
- Added system prompt support to chat request construction.
- Documented preset behavior and limitations.
```

- [ ] **Step 4: Run final verification**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp .pytest_cache/tmp
.\.venv\Scripts\python.exe -m compileall app.py ai_chat
.\.venv\Scripts\python.exe -m ruff check .
git status --short
```

Expected:

- pytest exits 0.
- compileall exits 0.
- Ruff exits 0.
- `git status --short` shows only `README.md` and `CHANGELOG.md` modified before commit.

- [ ] **Step 5: Commit Task 4**

Run:

```powershell
git add README.md CHANGELOG.md
git commit -m "docs: document prompt presets v1.6"
```

## Task 5: Push v1.6

**Files:**
- No source changes unless final verification finds a defect.

- [ ] **Step 1: Confirm clean state and recent commits**

Run:

```powershell
git status --short
git log --oneline -8
```

Expected:

- `git status --short` is empty.
- Recent commits include v1.6 design, plan, preset catalog, chat prompt support, preset sidebar, and docs.

- [ ] **Step 2: Push**

Run:

```powershell
git push
```

Expected:

- Local `main` pushes to `origin/main`.
- No extra commit is created for this push-only task.
