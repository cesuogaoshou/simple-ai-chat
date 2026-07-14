# Deployment Readiness v1.3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prepare Simple AI Chat for repeatable Streamlit Cloud deployment with safe example secrets, runtime diagnostics, and deployment documentation.

**Architecture:** Keep the existing Streamlit app boundaries. Add `ai_chat/runtime.py` for display-safe runtime detection, wire it into the sidebar in `app.py`, and add Streamlit deployment config plus documentation files without changing chat behavior.

**Tech Stack:** Python, Streamlit, pytest, Ruff, GitHub Actions, Streamlit Cloud.

---

## File Structure

- Create `.streamlit/config.toml`: safe Streamlit app defaults for local and hosted runs.
- Create `.streamlit/secrets.toml.example`: placeholder-only Streamlit Cloud secrets example.
- Create `ai_chat/runtime.py`: safe runtime detection helper.
- Create `tests/test_runtime.py`: tests for runtime labels and secret safety.
- Modify `app.py`: display runtime label in the sidebar.
- Modify `README.md`: add Streamlit Cloud deployment instructions.
- Modify `CHANGELOG.md`: add v1.3 notes.

## Task 1: Streamlit Deployment Files

**Files:**
- Create: `.streamlit/config.toml`
- Create: `.streamlit/secrets.toml.example`
- Modify: `.gitignore`

- [ ] **Step 1: Create `.streamlit/config.toml`**

Create `.streamlit/config.toml`:

```toml
[server]
headless = true

[browser]
gatherUsageStats = false
```

- [ ] **Step 2: Create `.streamlit/secrets.toml.example`**

Create `.streamlit/secrets.toml.example`:

```toml
AI_PROVIDER = "deepseek"

DEEPSEEK_API_KEY = "your_deepseek_api_key"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-v4-pro"

OPENAI_API_KEY = "your_openai_api_key"
OPENAI_BASE_URL = "https://api.openai.com/v1"
OPENAI_MODEL = "gpt-5.6"
```

- [ ] **Step 3: Confirm real Streamlit secrets stay ignored**

Run:

```powershell
git check-ignore .streamlit/secrets.toml
```

Expected: prints `.streamlit/secrets.toml`.

If it does not print `.streamlit/secrets.toml`, add this line to `.gitignore`:

```text
.streamlit/secrets.toml
```

- [ ] **Step 4: Verify and commit**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall app.py ai_chat
.\.venv\Scripts\python.exe -m ruff check .
```

Expected: all commands exit 0.

Commit:

```powershell
git add .streamlit/config.toml .streamlit/secrets.toml.example .gitignore
git commit -m "chore: add streamlit deployment config"
```

## Task 2: Runtime Diagnostics

**Files:**
- Create: `ai_chat/runtime.py`
- Create: `tests/test_runtime.py`
- Modify: `app.py`

- [ ] **Step 1: Add failing runtime tests**

Create `tests/test_runtime.py`:

```python
from ai_chat.runtime import RuntimeInfo, detect_runtime


def test_detect_runtime_defaults_to_local(monkeypatch):
    clear_runtime_env(monkeypatch)

    runtime = detect_runtime()

    assert runtime == RuntimeInfo(name="local", label="Runtime: local")


def test_detect_runtime_reports_streamlit_cloud(monkeypatch):
    clear_runtime_env(monkeypatch)
    monkeypatch.setenv("STREAMLIT_CLOUD", "1")

    runtime = detect_runtime()

    assert runtime == RuntimeInfo(name="streamlit-cloud", label="Runtime: streamlit-cloud")


def test_runtime_label_does_not_include_secret_values(monkeypatch):
    clear_runtime_env(monkeypatch)
    monkeypatch.setenv("STREAMLIT_CLOUD", "1")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "super-secret-key")

    runtime = detect_runtime()

    assert "super-secret-key" not in runtime.label


def clear_runtime_env(monkeypatch):
    for key in ["STREAMLIT_CLOUD", "DEEPSEEK_API_KEY", "OPENAI_API_KEY"]:
        monkeypatch.delenv(key, raising=False)
```

- [ ] **Step 2: Run runtime tests to verify failure**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_runtime.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 'ai_chat.runtime'`.

- [ ] **Step 3: Implement runtime helper**

Create `ai_chat/runtime.py`:

```python
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeInfo:
    name: str
    label: str


def detect_runtime() -> RuntimeInfo:
    if os.getenv("STREAMLIT_CLOUD"):
        return RuntimeInfo(name="streamlit-cloud", label="Runtime: streamlit-cloud")
    return RuntimeInfo(name="local", label="Runtime: local")
```

- [ ] **Step 4: Display runtime label in sidebar**

In `app.py`, add the import:

```python
from ai_chat.runtime import detect_runtime
```

In `render_sidebar()`, directly under `st.header("Configuration")`, add:

```python
        st.caption(detect_runtime().label)
```

- [ ] **Step 5: Verify and commit**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_runtime.py -q
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall app.py ai_chat
.\.venv\Scripts\python.exe -m ruff check .
```

Expected: all commands exit 0.

Commit:

```powershell
git add ai_chat/runtime.py tests/test_runtime.py app.py
git commit -m "feat: add safe runtime diagnostics"
```

## Task 3: Deployment Documentation

**Files:**
- Modify: `README.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Add README deployment section**

Add this section to `README.md` before `## Project Structure`:

```markdown
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
```

- [ ] **Step 2: Update README feature list**

Add these bullets under `## Features`:

```markdown
- Streamlit Cloud deployment configuration
- Safe runtime diagnostics for local and Streamlit Cloud runs
```

- [ ] **Step 3: Update changelog**

Add this section at the top of `CHANGELOG.md`, after `# Changelog`:

```markdown
## v1.3 - Deployment Readiness

- Added Streamlit deployment configuration.
- Added Streamlit secrets template.
- Added safe runtime diagnostics.
- Added Streamlit Cloud deployment documentation.
```

- [ ] **Step 4: Verify and commit**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall app.py ai_chat
.\.venv\Scripts\python.exe -m ruff check .
```

Expected: all commands exit 0.

Commit:

```powershell
git add README.md CHANGELOG.md
git commit -m "docs: document deployment readiness v1.3"
```

## Task 4: Final Verification and Push

**Files:**
- No code changes unless verification reveals a defect.

- [ ] **Step 1: Run full verification**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall app.py ai_chat
.\.venv\Scripts\python.exe -m ruff check .
git check-ignore .streamlit/secrets.toml
git status --short
git log --oneline -8
```

Expected:

- `pytest`: all tests pass.
- `compileall`: exits 0.
- `ruff check`: exits 0.
- `git check-ignore`: prints `.streamlit/secrets.toml`.
- `git status --short`: empty.
- Recent commits include v1.3 config, runtime diagnostics, and docs commits.

- [ ] **Step 2: Push to GitHub**

Run:

```powershell
git push
```

Expected: local `main` pushes to `origin/main`.
