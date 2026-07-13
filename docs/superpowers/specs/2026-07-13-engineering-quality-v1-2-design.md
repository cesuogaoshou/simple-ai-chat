# Engineering Quality v1.2 Design

## Summary

v1.2 turns Simple AI Chat from a runnable demo into a more maintainable project template. The release focuses on configuration visibility, defensive validation, code quality tooling, CI, and release documentation. It does not change the core Streamlit + OpenAI-compatible Chat Completions architecture.

## Goals

- Show a safe configuration diagnostic in the sidebar.
- Validate generation settings in code, not only through Streamlit widgets.
- Add `ruff` as the project lint tool.
- Add GitHub Actions CI for tests, compile checks, and linting.
- Add a `CHANGELOG.md` covering v1.0, v1.1, and v1.2.
- Update README with the new quality and maintenance workflow.

## Non-Goals

- No deployment setup.
- No RAG, file upload, vector database, or tool calling.
- No persistent storage or multi-session management.
- No frontend framework migration.
- No secrets or real API keys in CI.

## User Experience

The sidebar will keep the current Provider, model, and Base URL display. v1.2 adds a configuration status line that reports whether the active Provider has an API key configured. It must not display the key value or any masked key fragments.

If the selected Provider is invalid or the active API key is missing, the existing warning behavior remains. The diagnostic should help users understand the state before they send a message.

## Architecture

The existing boundaries remain:

- `ai_chat/config.py`: provider configuration parsing and safe diagnostics.
- `ai_chat/chat.py`: generation settings and chat helpers.
- `app.py`: Streamlit rendering and sidebar controls.

v1.2 adds:

- A small config diagnostic helper that returns display-safe status data.
- Validation for `GenerationSettings`, raising `ValueError` when values are outside supported bounds.
- A `pyproject.toml` with `ruff` settings.
- `.github/workflows/ci.yml` for automated checks.
- `CHANGELOG.md` for release history.

## Validation Rules

`GenerationSettings` will enforce:

- `temperature` must be between `0.0` and `2.0`, inclusive.
- `max_tokens` must be between `128` and `8192`, inclusive.

Streamlit controls already constrain UI input, but these rules protect tests, future callers, and direct module use.

## CI

GitHub Actions will run on `push` and `pull_request` to `main`.

The CI job will:

- Set up Python.
- Install dependencies from `requirements.txt`.
- Run `python -m pytest -q`.
- Run `python -m compileall app.py ai_chat`.
- Run `python -m ruff check .`.

CI does not need real API keys because unit tests use fake clients and configuration tests use monkeypatched environment variables.

## Documentation

README will document:

- Sidebar configuration diagnostics.
- Generation settings validation bounds.
- Local lint command.
- CI checks.

`CHANGELOG.md` will summarize:

- v1.0 initial simple chat.
- v1.1 streaming, generation controls, Markdown export.
- v1.2 engineering quality improvements.

## Testing

Unit tests will cover:

- Safe diagnostic output does not include API key values.
- Diagnostic reports active Provider status.
- `GenerationSettings` accepts boundary values.
- `GenerationSettings` rejects out-of-range values.

Verification will cover:

- `pytest` passes.
- `compileall` passes.
- `ruff check .` passes.
- Git status is clean before push.

## Acceptance Criteria

- Configuration diagnostics are visible in the sidebar without leaking secrets.
- Invalid generation settings fail fast with clear `ValueError` messages.
- `ruff` is installed through project requirements and configured in `pyproject.toml`.
- GitHub Actions CI exists and matches local verification commands.
- `CHANGELOG.md` and README describe v1.2.
- All local checks pass before commit and push.
