# Deployment Readiness v1.3 Design

## Summary

v1.3 prepares Simple AI Chat for repeatable deployment without changing the core Streamlit chat architecture. The release focuses on Streamlit Cloud documentation, example secrets, safe runtime diagnostics, and release notes.

## Goals

- Add Streamlit deployment configuration.
- Provide a safe `secrets.toml` example for Streamlit Cloud.
- Keep real secrets out of Git.
- Show a small runtime environment diagnostic in the sidebar.
- Document deployment steps for Streamlit Cloud.
- Update `CHANGELOG.md` for v1.3.

## Non-Goals

- No Docker setup.
- No Render, Railway, Fly.io, or VPS deployment.
- No database or persistent storage.
- No multi-user auth.
- No RAG, file upload, or vector search.
- No frontend framework migration.

## Deployment Target

v1.3 targets Streamlit Cloud as the primary deployment path because the app is already a Streamlit app and can run from `app.py` with `requirements.txt`.

The deployment documentation will cover:

- Creating a Streamlit Cloud app from the GitHub repository.
- Setting the main file path to `app.py`.
- Adding provider secrets in Streamlit Cloud.
- Choosing DeepSeek or OpenAI through `AI_PROVIDER`.
- Confirming that no real `.env` or `.streamlit/secrets.toml` file is committed.

## Configuration Files

Add `.streamlit/config.toml` for deploy-friendly defaults:

- headless server mode.
- default port config suitable for Streamlit-managed environments.
- optional browser telemetry suppression if supported by Streamlit config.

Add `.streamlit/secrets.toml.example` as documentation-only sample content:

- `AI_PROVIDER`
- `DEEPSEEK_API_KEY`
- `DEEPSEEK_BASE_URL`
- `DEEPSEEK_MODEL`
- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `OPENAI_MODEL`

The existing `.gitignore` already ignores `.streamlit/secrets.toml`; v1.3 will keep that rule and document it.

## Runtime Diagnostic

The sidebar will show a small runtime label:

- `Runtime: local` when running from local `.env`/developer environment.
- `Runtime: streamlit-cloud` when Streamlit Cloud indicators are present.
- `Runtime: unknown` when neither signal is clear.

The diagnostic must not reveal secrets, environment variable values, hostnames, or user-specific paths.

Implementation should keep this logic in a small helper function so it can be unit-tested without Streamlit.

## Architecture

Keep existing boundaries:

- `app.py`: sidebar rendering.
- `ai_chat/config.py`: provider config and safe provider diagnostics.
- `ai_chat/chat.py`: chat request helpers.

Add a small runtime helper module if needed:

- `ai_chat/runtime.py`: safe runtime detection and label formatting.

This keeps deployment/environment concerns separate from provider parsing.

## Documentation

README will gain a `Deployment` section with Streamlit Cloud steps and secrets examples.

`CHANGELOG.md` will add:

- v1.3 deployment configuration.
- v1.3 Streamlit Cloud documentation.
- v1.3 runtime diagnostic.

## Testing

Unit tests will cover:

- runtime detection returns `local` when no cloud signal exists.
- runtime detection returns `streamlit-cloud` when a Streamlit Cloud environment signal is present.
- runtime labels never include secret values.

Verification will cover:

- `python -m pytest -q`
- `python -m compileall app.py ai_chat`
- `python -m ruff check .`
- `git status --short`
- confirming `.streamlit/secrets.toml` remains ignored.

## Acceptance Criteria

- `.streamlit/config.toml` exists and is safe to commit.
- `.streamlit/secrets.toml.example` exists and contains only placeholder values.
- `.streamlit/secrets.toml` remains ignored.
- Sidebar displays a safe runtime label.
- README explains how to deploy on Streamlit Cloud.
- CHANGELOG includes v1.3.
- All local checks pass before commit and push.
