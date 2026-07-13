# Engineering Quality v1.2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add safe configuration diagnostics, generation settings validation, Ruff linting, GitHub Actions CI, and release documentation.

**Architecture:** Keep the existing Streamlit app structure. `ai_chat/config.py` will expose a display-safe diagnostic helper, `ai_chat/chat.py` will enforce `GenerationSettings` bounds, and project-level files will define linting, CI, changelog, and documentation updates.

**Tech Stack:** Python, Streamlit, OpenAI Python SDK, pytest, Ruff, GitHub Actions.

---

## File Structure

- Modify `ai_chat/config.py`: add `ProviderDiagnostic` and `get_provider_diagnostic()`.
- Modify `tests/test_config.py`: test diagnostic status and secret safety.
- Modify `ai_chat/chat.py`: validate `GenerationSettings` bounds.
- Modify `tests/test_chat.py`: test accepted boundary values and rejected invalid values.
- Modify `app.py`: display safe configuration status in the sidebar.
- Modify `requirements.txt`: add `ruff`.
- Create `pyproject.toml`: configure Ruff.
- Create `.github/workflows/ci.yml`: run tests, compile check, and Ruff.
- Create `CHANGELOG.md`: document v1.0, v1.1, and v1.2.
- Modify `README.md`: document diagnostics, validation, linting, and CI.

## Task 1: Safe Provider Diagnostics

**Files:**
- Modify: `tests/test_config.py`
- Modify: `ai_chat/config.py`
- Modify: `app.py`

- [ ] **Step 1: Add failing diagnostic tests**

Append this to `tests/test_config.py`:

```python
from ai_chat.config import get_provider_diagnostic


def test_provider_diagnostic_reports_configured_key_without_leaking_secret(monkeypatch):
    clear_ai_env(monkeypatch)
    monkeypatch.setenv("AI_PROVIDER", "deepseek")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "super-secret-key")

    diagnostic = get_provider_diagnostic()

    assert diagnostic.provider == "deepseek"
    assert diagnostic.api_key_name == "DEEPSEEK_API_KEY"
    assert diagnostic.has_api_key is True
    assert "super-secret-key" not in diagnostic.status_text


def test_provider_diagnostic_reports_missing_key(monkeypatch):
    clear_ai_env(monkeypatch)
    monkeypatch.setenv("AI_PROVIDER", "openai")

    diagnostic = get_provider_diagnostic()

    assert diagnostic.provider == "openai"
    assert diagnostic.api_key_name == "OPENAI_API_KEY"
    assert diagnostic.has_api_key is False
    assert diagnostic.status_text == "OPENAI_API_KEY is not configured."
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_config.py -q
```

Expected: FAIL with import error for `get_provider_diagnostic`.

- [ ] **Step 3: Implement provider diagnostics**

Add this to `ai_chat/config.py` after `ProviderConfig`:

```python
@dataclass(frozen=True)
class ProviderDiagnostic:
    provider: str
    api_key_name: str
    has_api_key: bool
    status_text: str
```

Add this function before `load_provider_config()`:

```python
def get_provider_diagnostic() -> ProviderDiagnostic:
    provider = os.getenv("AI_PROVIDER", "deepseek").strip().lower()
    if provider not in SUPPORTED_PROVIDERS:
        return ProviderDiagnostic(
            provider=provider,
            api_key_name="",
            has_api_key=False,
            status_text=f"Unsupported AI_PROVIDER '{provider}'.",
        )

    api_key_name = f"{provider.upper()}_API_KEY"
    has_api_key = bool(os.getenv(api_key_name, "").strip())
    status = f"{api_key_name} is configured." if has_api_key else f"{api_key_name} is not configured."
    return ProviderDiagnostic(
        provider=provider,
        api_key_name=api_key_name,
        has_api_key=has_api_key,
        status_text=status,
    )
```

- [ ] **Step 4: Display diagnostics in sidebar**

In `app.py`, import `get_provider_diagnostic`:

```python
from ai_chat.config import ProviderConfig, get_provider_diagnostic, load_provider_config
```

In `render_sidebar()`, after the Provider/model/Base URL block, add:

```python
        diagnostic = get_provider_diagnostic()
        if diagnostic.has_api_key:
            st.success(diagnostic.status_text)
        else:
            st.warning(diagnostic.status_text)
```

- [ ] **Step 5: Verify and commit**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_config.py -q
.\.venv\Scripts\python.exe -m compileall app.py ai_chat
```

Expected: both commands exit 0.

Commit:

```powershell
git add ai_chat/config.py tests/test_config.py app.py
git commit -m "feat: add safe provider diagnostics"
```

## Task 2: Generation Settings Validation

**Files:**
- Modify: `tests/test_chat.py`
- Modify: `ai_chat/chat.py`

- [ ] **Step 1: Add failing validation tests**

Append this to `tests/test_chat.py`:

```python
import pytest


def test_generation_settings_accepts_boundary_values():
    assert GenerationSettings(temperature=0.0, max_tokens=128).temperature == 0.0
    assert GenerationSettings(temperature=2.0, max_tokens=8192).max_tokens == 8192


def test_generation_settings_rejects_temperature_out_of_range():
    with pytest.raises(ValueError, match="temperature"):
        GenerationSettings(temperature=-0.1)

    with pytest.raises(ValueError, match="temperature"):
        GenerationSettings(temperature=2.1)


def test_generation_settings_rejects_max_tokens_out_of_range():
    with pytest.raises(ValueError, match="max_tokens"):
        GenerationSettings(max_tokens=127)

    with pytest.raises(ValueError, match="max_tokens"):
        GenerationSettings(max_tokens=8193)
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_chat.py -q
```

Expected: FAIL because invalid settings do not raise yet.

- [ ] **Step 3: Implement validation**

Add this method to the existing `GenerationSettings` dataclass in `ai_chat/chat.py`:

```python
    def __post_init__(self) -> None:
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError("temperature must be between 0.0 and 2.0.")
        if not 128 <= self.max_tokens <= 8192:
            raise ValueError("max_tokens must be between 128 and 8192.")
```

- [ ] **Step 4: Verify and commit**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_chat.py -q
.\.venv\Scripts\python.exe -m compileall app.py ai_chat
```

Expected: both commands exit 0.

Commit:

```powershell
git add ai_chat/chat.py tests/test_chat.py
git commit -m "feat: validate generation settings"
```

## Task 3: Ruff Tooling

**Files:**
- Modify: `requirements.txt`
- Create: `pyproject.toml`

- [ ] **Step 1: Add Ruff dependency**

Append this line to `requirements.txt`:

```text
ruff>=0.9.0
```

- [ ] **Step 2: Add Ruff configuration**

Create `pyproject.toml`:

```toml
[tool.ruff]
line-length = 120
target-version = "py313"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]
ignore = []
```

- [ ] **Step 3: Install dependencies if needed**

Run:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Expected: exits 0 and installs `ruff` if it is not already present.

- [ ] **Step 4: Run Ruff**

Run:

```powershell
.\.venv\Scripts\python.exe -m ruff check .
```

Expected: exits 0. If Ruff reports import ordering or style issues, apply the smallest code changes needed and rerun.

- [ ] **Step 5: Verify and commit**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall app.py ai_chat
.\.venv\Scripts\python.exe -m ruff check .
```

Expected: all commands exit 0.

Commit:

```powershell
git add requirements.txt pyproject.toml
git commit -m "chore: add ruff linting"
```

## Task 4: GitHub Actions CI

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Add CI workflow**

Create `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: ["main"]
  pull_request:
    branches: ["main"]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Check out repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.13"

      - name: Install dependencies
        run: python -m pip install -r requirements.txt

      - name: Run tests
        run: python -m pytest -q

      - name: Compile Python files
        run: python -m compileall app.py ai_chat

      - name: Run Ruff
        run: python -m ruff check .
```

- [ ] **Step 2: Verify local commands match CI**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall app.py ai_chat
.\.venv\Scripts\python.exe -m ruff check .
```

Expected: all commands exit 0.

- [ ] **Step 3: Commit CI**

Run:

```powershell
git add .github/workflows/ci.yml
git commit -m "ci: add python quality workflow"
```

## Task 5: Changelog and README Updates

**Files:**
- Create: `CHANGELOG.md`
- Modify: `README.md`

- [ ] **Step 1: Add changelog**

Create `CHANGELOG.md`:

```markdown
# Changelog

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
```

- [ ] **Step 2: Update README maintenance section**

Add this section to `README.md` before `## Troubleshooting`:

```markdown
## Quality Checks

Run the same checks locally that CI runs on GitHub:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall app.py ai_chat
.\.venv\Scripts\python.exe -m ruff check .
```

The GitHub Actions workflow runs these checks on pushes and pull requests to `main`.
```

Add this paragraph under `## Generation Settings`:

```markdown
The app validates these settings in code as well as in the UI. `temperature` must be between `0.0` and `2.0`; `max_tokens` must be between `128` and `8192`.
```

Add this paragraph after the environment variables table:

```markdown
The sidebar shows whether the active provider API key is configured. It never displays the key value or a masked key fragment.
```

- [ ] **Step 3: Verify and commit**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall app.py ai_chat
.\.venv\Scripts\python.exe -m ruff check .
```

Expected: all commands exit 0.

Commit:

```powershell
git add CHANGELOG.md README.md
git commit -m "docs: document engineering quality v1.2"
```

## Task 6: Final Verification and Push

**Files:**
- No code changes unless verification reveals a defect.

- [ ] **Step 1: Run full verification**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall app.py ai_chat
.\.venv\Scripts\python.exe -m ruff check .
git status --short
git log --oneline -8
```

Expected:

- `pytest`: all tests pass.
- `compileall`: exits 0.
- `ruff check`: exits 0.
- `git status --short`: empty.
- Recent commits include v1.2 diagnostic, validation, Ruff, CI, and docs commits.

- [ ] **Step 2: Push to GitHub**

Run:

```powershell
git push
```

Expected: local `main` pushes to `origin/main`.
