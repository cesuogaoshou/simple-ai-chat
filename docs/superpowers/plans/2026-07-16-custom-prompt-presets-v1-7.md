# Custom Prompt Presets v1.7 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add local reusable custom prompt presets that can be saved, selected, and deleted without changing chat session storage.

**Architecture:** Add a pure `ai_chat.preset_store` module for `.data/presets.json` persistence, then extend `ai_chat.presets` so built-in and custom runtime presets share one catalog interface. Wire the merged preset catalog into the Streamlit sidebar while keeping request-time system prompt resolution and `.data/chats.json` unchanged.

**Tech Stack:** Python, Streamlit, pytest, Ruff, local JSON storage.

---

## File Structure

- Create `ai_chat/preset_store.py`: local custom preset persistence, validation, ID handling, deletion, and conversion to runtime `PromptPreset`.
- Create `tests/test_preset_store.py`: unit tests for missing files, save/load round trips, corrupt JSON backup, ID regeneration, blank prompt rejection, blank name fallback, deletion, and runtime conversion.
- Modify `ai_chat/presets.py`: accept optional custom runtime presets in `list_presets`, `get_preset`, and `resolve_system_prompt`.
- Modify `tests/test_presets.py`: verify built-in plus custom catalog behavior.
- Modify `app.py`: load `.data/presets.json`, render custom preset save/delete controls, pass custom presets into prompt resolution, and persist only custom preset records.
- Modify `README.md`: document custom preset persistence and local behavior.
- Modify `CHANGELOG.md`: add v1.7 release notes.

Use `.\.venv\Scripts\python.exe -m pytest -q --basetemp .pytest_cache/tmp` for test runs in this workspace because the default Windows temp directory can raise permission errors.

## Task 1: Custom Preset Store

**Files:**
- Create: `ai_chat/preset_store.py`
- Create: `tests/test_preset_store.py`

- [ ] **Step 1: Write failing preset store tests**

Create `tests/test_preset_store.py`:

```python
import json

from ai_chat.preset_store import (
    CUSTOM_PRESET_DESCRIPTION,
    CUSTOM_PRESET_ID_PREFIX,
    CustomPromptPreset,
    create_custom_preset,
    custom_to_prompt_preset,
    delete_custom_preset,
    is_custom_preset_id,
    load_custom_presets,
    save_custom_presets,
)


def test_load_custom_presets_returns_empty_for_missing_file(tmp_path):
    assert load_custom_presets(tmp_path / "presets.json", reserved_ids=set()) == []


def test_save_and_load_custom_presets_round_trips(tmp_path):
    path = tmp_path / "presets.json"
    preset = CustomPromptPreset(
        id="custom_reviewer",
        name="Reviewer",
        description=CUSTOM_PRESET_DESCRIPTION,
        system_prompt="Review the code.",
        created_at="2026-07-16T00:00:00Z",
        updated_at="2026-07-16T00:00:00Z",
    )

    save_custom_presets(path, [preset])
    loaded = load_custom_presets(path, reserved_ids=set())

    assert loaded == [preset]


def test_create_custom_preset_rejects_blank_prompt():
    assert create_custom_preset("Reviewer", "   ", existing_ids=set()) is None


def test_create_custom_preset_falls_back_for_blank_name():
    preset = create_custom_preset("   ", "Review code.", existing_ids=set())

    assert preset is not None
    assert preset.name == "Custom preset"
    assert preset.description == CUSTOM_PRESET_DESCRIPTION
    assert preset.system_prompt == "Review code."
    assert preset.id.startswith(CUSTOM_PRESET_ID_PREFIX)
    assert preset.created_at
    assert preset.updated_at == preset.created_at


def test_load_custom_presets_regenerates_reserved_and_duplicate_ids(tmp_path):
    path = tmp_path / "presets.json"
    payload = {
        "presets": [
            {
                "id": "general",
                "name": "Reserved",
                "description": "Custom prompt preset.",
                "system_prompt": "First prompt.",
                "created_at": "2026-07-16T00:00:00Z",
                "updated_at": "2026-07-16T00:00:00Z",
            },
            {
                "id": "custom_same",
                "name": "First",
                "description": "Custom prompt preset.",
                "system_prompt": "Second prompt.",
                "created_at": "2026-07-16T00:00:00Z",
                "updated_at": "2026-07-16T00:00:00Z",
            },
            {
                "id": "custom_same",
                "name": "Second",
                "description": "Custom prompt preset.",
                "system_prompt": "Third prompt.",
                "created_at": "2026-07-16T00:00:00Z",
                "updated_at": "2026-07-16T00:00:00Z",
            },
        ]
    }
    path.write_text(json.dumps(payload), encoding="utf-8")

    loaded = load_custom_presets(path, reserved_ids={"general"})
    loaded_ids = [preset.id for preset in loaded]

    assert len(loaded) == 3
    assert "general" not in loaded_ids
    assert len(set(loaded_ids)) == 3
    assert all(preset.id.startswith(CUSTOM_PRESET_ID_PREFIX) for preset in loaded)


def test_load_custom_presets_backs_up_corrupt_file(tmp_path):
    path = tmp_path / "presets.json"
    path.write_text("{not-json", encoding="utf-8")

    loaded = load_custom_presets(path, reserved_ids=set())

    assert loaded == []
    assert (tmp_path / "presets.invalid.json").exists()


def test_delete_custom_preset_removes_requested_id():
    first = CustomPromptPreset(
        id="custom_first",
        name="First",
        description=CUSTOM_PRESET_DESCRIPTION,
        system_prompt="First prompt.",
        created_at="2026-07-16T00:00:00Z",
        updated_at="2026-07-16T00:00:00Z",
    )
    second = CustomPromptPreset(
        id="custom_second",
        name="Second",
        description=CUSTOM_PRESET_DESCRIPTION,
        system_prompt="Second prompt.",
        created_at="2026-07-16T00:00:00Z",
        updated_at="2026-07-16T00:00:00Z",
    )

    assert delete_custom_preset([first, second], "custom_first") == [second]


def test_is_custom_preset_id_checks_prefix():
    assert is_custom_preset_id("custom_abc") is True
    assert is_custom_preset_id("general") is False


def test_custom_to_prompt_preset_drops_timestamps():
    custom = CustomPromptPreset(
        id="custom_reviewer",
        name="Reviewer",
        description=CUSTOM_PRESET_DESCRIPTION,
        system_prompt="Review the code.",
        created_at="2026-07-16T00:00:00Z",
        updated_at="2026-07-16T00:00:00Z",
    )

    runtime = custom_to_prompt_preset(custom)

    assert runtime.id == "custom_reviewer"
    assert runtime.name == "Reviewer"
    assert runtime.description == CUSTOM_PRESET_DESCRIPTION
    assert runtime.system_prompt == "Review the code."
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_preset_store.py -q --basetemp .pytest_cache/tmp
```

Expected: FAIL with `ModuleNotFoundError: No module named 'ai_chat.preset_store'`.

- [ ] **Step 3: Implement preset store module**

Create `ai_chat/preset_store.py`:

```python
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from ai_chat.presets import PromptPreset

CUSTOM_PRESET_ID_PREFIX = "custom_"
CUSTOM_PRESET_DESCRIPTION = "Custom prompt preset."
DEFAULT_CUSTOM_PRESET_NAME = "Custom preset"


@dataclass(frozen=True)
class CustomPromptPreset:
    id: str
    name: str
    description: str
    system_prompt: str
    created_at: str
    updated_at: str


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def is_custom_preset_id(preset_id: str) -> bool:
    return preset_id.startswith(CUSTOM_PRESET_ID_PREFIX)


def safe_custom_name(name: str) -> str:
    cleaned = name.strip()
    return cleaned or DEFAULT_CUSTOM_PRESET_NAME


def new_custom_preset_id(existing_ids: set[str]) -> str:
    while True:
        preset_id = f"{CUSTOM_PRESET_ID_PREFIX}{uuid4()}"
        if preset_id not in existing_ids:
            return preset_id


def create_custom_preset(
    name: str, system_prompt: str, existing_ids: set[str]
) -> CustomPromptPreset | None:
    prompt = system_prompt.strip()
    if not prompt:
        return None
    now = utc_now()
    return CustomPromptPreset(
        id=new_custom_preset_id(existing_ids),
        name=safe_custom_name(name),
        description=CUSTOM_PRESET_DESCRIPTION,
        system_prompt=prompt,
        created_at=now,
        updated_at=now,
    )


def custom_preset_to_dict(preset: CustomPromptPreset) -> dict[str, str]:
    return {
        "id": preset.id,
        "name": preset.name,
        "description": preset.description,
        "system_prompt": preset.system_prompt,
        "created_at": preset.created_at,
        "updated_at": preset.updated_at,
    }


def custom_preset_from_dict(
    data: dict[str, object], existing_ids: set[str], reserved_ids: set[str]
) -> CustomPromptPreset | None:
    prompt = str(data.get("system_prompt", "")).strip()
    if not prompt:
        return None

    preset_id = str(data.get("id", "")).strip()
    if (
        not is_custom_preset_id(preset_id)
        or preset_id in existing_ids
        or preset_id in reserved_ids
    ):
        preset_id = new_custom_preset_id(existing_ids | reserved_ids)

    now = utc_now()
    return CustomPromptPreset(
        id=preset_id,
        name=safe_custom_name(str(data.get("name", ""))),
        description=str(data.get("description") or CUSTOM_PRESET_DESCRIPTION),
        system_prompt=prompt,
        created_at=str(data.get("created_at") or now),
        updated_at=str(data.get("updated_at") or now),
    )


def load_custom_presets(path: Path, reserved_ids: set[str]) -> list[CustomPromptPreset]:
    if not path.exists():
        return []

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        backup = path.with_name(f"{path.stem}.invalid{path.suffix}")
        path.replace(backup)
        return []

    raw_presets = payload.get("presets", []) if isinstance(payload, dict) else []
    presets = []
    seen_ids: set[str] = set()
    for raw_preset in raw_presets:
        if isinstance(raw_preset, dict):
            preset = custom_preset_from_dict(raw_preset, seen_ids, reserved_ids)
            if preset is not None:
                presets.append(preset)
                seen_ids.add(preset.id)
    return presets


def save_custom_presets(path: Path, presets: list[CustomPromptPreset]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"presets": [custom_preset_to_dict(preset) for preset in presets]}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def delete_custom_preset(
    presets: list[CustomPromptPreset], preset_id: str
) -> list[CustomPromptPreset]:
    return [preset for preset in presets if preset.id != preset_id]


def custom_to_prompt_preset(preset: CustomPromptPreset) -> PromptPreset:
    return PromptPreset(
        id=preset.id,
        name=preset.name,
        description=preset.description,
        system_prompt=preset.system_prompt,
    )
```

- [ ] **Step 4: Verify preset store tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_preset_store.py -q --basetemp .pytest_cache/tmp
.\.venv\Scripts\python.exe -m ruff check .
```

Expected:

- `tests/test_preset_store.py`: all tests pass.
- Ruff exits 0.

- [ ] **Step 5: Commit Task 1**

Run:

```powershell
git add ai_chat/preset_store.py tests/test_preset_store.py
git commit -m "feat: add custom prompt preset store"
```

## Task 2: Preset Catalog Custom Preset Integration

**Files:**
- Modify: `ai_chat/presets.py`
- Modify: `tests/test_presets.py`

- [ ] **Step 1: Add failing custom catalog tests**

In `tests/test_presets.py`, add `PromptPreset` to the existing import block:

```python
from ai_chat.presets import (
    BUILT_IN_PRESETS,
    DEFAULT_PRESET_ID,
    PromptPreset,
    get_preset,
    list_presets,
    resolve_system_prompt,
)
```

Append these tests to the end of the file:

```python
def custom_preset() -> PromptPreset:
    return PromptPreset(
        id="custom_reviewer",
        name="Reviewer",
        description="Custom prompt preset.",
        system_prompt="Review code carefully.",
    )


def test_list_presets_appends_custom_presets_after_built_ins():
    presets = list_presets([custom_preset()])

    assert presets[: len(BUILT_IN_PRESETS)] == list(BUILT_IN_PRESETS)
    assert presets[-1] == custom_preset()


def test_get_preset_returns_custom_preset():
    preset = get_preset("custom_reviewer", [custom_preset()])

    assert preset == custom_preset()


def test_get_preset_falls_back_with_custom_presets_present():
    assert get_preset("missing", [custom_preset()]) == get_preset(DEFAULT_PRESET_ID)


def test_resolve_system_prompt_uses_custom_preset():
    assert (
        resolve_system_prompt("custom_reviewer", custom_presets=[custom_preset()])
        == "Review code carefully."
    )


def test_resolve_system_prompt_custom_text_overrides_custom_preset():
    assert (
        resolve_system_prompt(
            "custom_reviewer",
            "  One-off prompt  ",
            custom_presets=[custom_preset()],
        )
        == "One-off prompt"
    )
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_presets.py -q --basetemp .pytest_cache/tmp
```

Expected: FAIL because `list_presets`, `get_preset`, and `resolve_system_prompt` do not accept custom preset arguments yet.

- [ ] **Step 3: Update preset catalog helpers**

In `ai_chat/presets.py`, update imports and helper signatures:

```python
from collections.abc import Sequence
from dataclasses import dataclass
```

Replace the three helper functions with:

```python
def list_presets(custom_presets: Sequence[PromptPreset] = ()) -> list[PromptPreset]:
    return [*BUILT_IN_PRESETS, *custom_presets]


def get_preset(
    preset_id: str, custom_presets: Sequence[PromptPreset] = ()
) -> PromptPreset:
    for preset in list_presets(custom_presets):
        if preset.id == preset_id:
            return preset
    return BUILT_IN_PRESETS[0]


def resolve_system_prompt(
    preset_id: str,
    custom_prompt: str = "",
    custom_presets: Sequence[PromptPreset] = (),
) -> str:
    cleaned = custom_prompt.strip()
    if cleaned:
        return cleaned
    return get_preset(preset_id, custom_presets).system_prompt
```

Do not change `BUILT_IN_PRESETS` or `DEFAULT_PRESET_ID`.

- [ ] **Step 4: Verify preset catalog tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_presets.py -q --basetemp .pytest_cache/tmp
.\.venv\Scripts\python.exe -m ruff check .
```

Expected:

- `tests/test_presets.py`: all tests pass.
- Ruff exits 0.

- [ ] **Step 5: Commit Task 2**

Run:

```powershell
git add ai_chat/presets.py tests/test_presets.py
git commit -m "feat: merge custom prompt presets into catalog"
```

## Task 3: Streamlit Custom Preset Management

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Update imports and storage constants**

In `app.py`, replace the preset import:

```python
from ai_chat.presets import DEFAULT_PRESET_ID, get_preset, list_presets, resolve_system_prompt
```

with:

```python
from ai_chat.preset_store import (
    create_custom_preset,
    custom_to_prompt_preset,
    delete_custom_preset,
    is_custom_preset_id,
    load_custom_presets,
    save_custom_presets,
)
from ai_chat.presets import (
    BUILT_IN_PRESETS,
    DEFAULT_PRESET_ID,
    get_preset,
    list_presets,
    resolve_system_prompt,
)
```

Add this constant after `SESSION_STORE`:

```python
PRESET_STORE = Path(".data/presets.json")
```

- [ ] **Step 2: Initialize custom preset state**

In `main()`, after `custom_system_prompt` initialization, add:

```python
    if "custom_presets" not in st.session_state:
        reserved_ids = {preset.id for preset in BUILT_IN_PRESETS}
        st.session_state.custom_presets = load_custom_presets(
            PRESET_STORE,
            reserved_ids=reserved_ids,
        )
    if "custom_preset_name" not in st.session_state:
        st.session_state.custom_preset_name = ""
```

- [ ] **Step 3: Add runtime custom preset helper**

Add this function before `active_system_prompt()`:

```python
def runtime_custom_presets():
    return [
        custom_to_prompt_preset(preset)
        for preset in st.session_state.custom_presets
    ]
```

- [ ] **Step 4: Resolve prompts with custom presets**

Replace `active_system_prompt()` with:

```python
def active_system_prompt() -> str:
    custom_prompt = (
        st.session_state.custom_system_prompt
        if st.session_state.use_custom_system_prompt
        else ""
    )
    return resolve_system_prompt(
        st.session_state.preset_id,
        custom_prompt,
        custom_presets=runtime_custom_presets(),
    )
```

- [ ] **Step 5: Update preset sidebar catalog rendering**

In `render_prompt_preset_sidebar()`, replace:

```python
    presets = list_presets()
```

with:

```python
    custom_presets = runtime_custom_presets()
    presets = list_presets(custom_presets)
```

Replace both calls to `get_preset(...)` in that function so they pass `custom_presets`:

```python
        format_func=lambda preset_id: get_preset(preset_id, custom_presets).name,
```

and:

```python
    st.caption(get_preset(selected_id, custom_presets).description)
```

- [ ] **Step 6: Add save custom preset controls**

In `render_prompt_preset_sidebar()`, inside the `if st.session_state.use_custom_system_prompt:` block, after the `st.text_area(...)` call, add:

```python
        st.text_input("Custom preset name", key="custom_preset_name")
        if st.button("Save as preset", use_container_width=True):
            existing_ids = {preset.id for preset in BUILT_IN_PRESETS}
            existing_ids.update(preset.id for preset in st.session_state.custom_presets)
            preset = create_custom_preset(
                st.session_state.custom_preset_name,
                st.session_state.custom_system_prompt,
                existing_ids,
            )
            if preset is None:
                st.warning("Enter a custom system prompt before saving a preset.")
            else:
                st.session_state.custom_presets.append(preset)
                save_custom_presets(PRESET_STORE, st.session_state.custom_presets)
                st.session_state.preset_id = preset.id
                st.session_state.use_custom_system_prompt = False
                st.session_state.custom_system_prompt = ""
                st.session_state.custom_preset_name = ""
                st.rerun()
```

- [ ] **Step 7: Add delete custom preset control**

In `render_prompt_preset_sidebar()`, after the custom prompt block, add:

```python
    if is_custom_preset_id(selected_id):
        if st.button("Delete custom preset", use_container_width=True):
            st.session_state.custom_presets = delete_custom_preset(
                st.session_state.custom_presets,
                selected_id,
            )
            save_custom_presets(PRESET_STORE, st.session_state.custom_presets)
            st.session_state.preset_id = DEFAULT_PRESET_ID
            st.rerun()
```

- [ ] **Step 8: Run verification**

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

- [ ] **Step 9: Commit Task 3**

Run:

```powershell
git add app.py
git commit -m "feat: add custom prompt preset sidebar controls"
```

## Task 4: Documentation and Final Verification

**Files:**
- Modify: `README.md`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Update README feature list**

In `README.md`, change:

```markdown
- Built-in prompt presets and custom system prompts
```

to:

```markdown
- Built-in prompt presets, saved custom presets, and custom system prompts
```

- [ ] **Step 2: Update README prompt presets section**

In `README.md`, replace the final paragraph of `## Prompt Presets`:

```markdown
The selected preset controls the system prompt sent with future model requests. You can also enable `Use custom system prompt` and enter a one-off custom instruction. Custom system prompts are local UI state in v1.6; they are not saved as named reusable presets and they are not stored in `.data/chats.json`.
```

with:

```markdown
The selected preset controls the system prompt sent with future model requests. You can also enable `Use custom system prompt` and enter a one-off custom instruction.

Custom prompts can be saved as named custom presets from the sidebar. Saved custom presets are stored locally in `.data/presets.json`, which is ignored by Git. Custom presets are not stored in `.data/chats.json`, so chat session import/export keeps the same shape as earlier versions.
```

- [ ] **Step 3: Update CHANGELOG**

Add this entry immediately after `# Changelog`:

```markdown
## v1.7 - Custom Prompt Presets

- Added local saved custom prompt presets.
- Added custom preset save and delete controls.
- Kept custom presets separate from chat session JSON.
- Documented local custom preset storage.
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
git commit -m "docs: document custom prompt presets v1.7"
```

## Task 5: Push v1.7

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
- Recent commits include v1.7 design, v1.7 plan, custom preset store, catalog integration, sidebar controls, and docs.

- [ ] **Step 2: Push**

Run:

```powershell
git push
```

Expected:

- Local `main` pushes to `origin/main`.
- No extra commit is created for this push-only task.
