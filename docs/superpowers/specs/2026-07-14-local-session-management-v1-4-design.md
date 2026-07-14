# Local Session Management v1.4 Design

## Summary

v1.4 adds local multi-session chat management to Simple AI Chat. Users will be able to create, switch, rename, delete, save, export, and import chat sessions without adding a database or user accounts. The feature keeps the app local-first and simple by storing session data in JSON under a gitignored `.data/` directory.

## Goals

- Support multiple local chat sessions.
- Persist sessions across app restarts using JSON.
- Let users create, switch, rename, and delete sessions from the sidebar.
- Keep the existing Markdown export.
- Add JSON export and JSON import for recoverable session transfer.
- Keep real chat data out of Git.
- Preserve the current Streamlit + OpenAI-compatible Chat Completions architecture.

## Non-Goals

- No database.
- No login or multi-user permissions.
- No cloud sync.
- No RAG, file upload, vector search, or tool calling.
- No frontend framework migration.
- No encryption for local session files in v1.4.

## Storage

Session data will be stored in:

```text
.data/chats.json
```

`.data/` must be added to `.gitignore` so local conversations are never committed.

The JSON file will contain a top-level object with a `sessions` array. Each session will include:

- `id`: stable UUID string.
- `title`: user-visible title.
- `messages`: list of `{role, content}` objects using the existing chat message shape.
- `created_at`: ISO timestamp.
- `updated_at`: ISO timestamp.

The app will create a default empty session when no storage file exists.

## User Experience

The sidebar will gain a `Sessions` section above generation controls:

- Session selector.
- `New chat` button.
- Rename input for the current session title.
- `Delete chat` button.
- `Export JSON` button.
- JSON import uploader.

Existing controls remain:

- Provider/configuration diagnostics.
- Runtime diagnostics.
- Generation settings.
- Clear chat.
- Markdown download.

Deleting the last session will create a new empty default session so the app always has an active session.

## Import and Export

Markdown export remains focused on human-readable conversation history.

JSON export will export the active session in the same schema used internally, so it can be imported later.

JSON import will:

- Accept one session object or a top-level object with a `sessions` array.
- Ignore empty messages.
- Generate a new session ID if the imported ID collides with an existing session.
- Use a safe fallback title when title is missing.

Invalid JSON or unsupported shapes will show a concise UI error and leave existing sessions unchanged.

## Architecture

Add a focused session module:

- `ai_chat/sessions.py`: session dataclasses, create/rename/delete helpers, JSON serialization, storage load/save, import/export helpers.

Keep `app.py` responsible for Streamlit UI only:

- Load sessions at startup.
- Store active session ID in `st.session_state`.
- Pass active session messages to existing chat helpers.
- Save sessions after message changes, rename, delete, import, and new session actions.

No changes are needed to `ai_chat/chat.py` except adapting call sites to use active session messages.

## Error Handling

- Missing `.data/chats.json`: create a default in-memory session and save on first mutation.
- Corrupt `.data/chats.json`: keep a backup path such as `.data/chats.invalid.json` and start with a default empty session.
- Invalid import JSON: show an error and do not mutate existing sessions.
- Delete active session: switch to another session or create a default session.
- Empty session title: use `Untitled chat`.

## Testing

Unit tests will cover:

- Creating a default session.
- Creating a new session with a unique ID.
- Renaming a session.
- Deleting a session while preserving at least one active session.
- Saving and loading `.data/chats.json`.
- Handling missing storage file.
- Handling corrupt storage file by falling back safely.
- Exporting active session JSON.
- Importing a valid session JSON.
- Rejecting invalid import JSON without mutating existing sessions.

Manual verification will cover:

- New chat appears in the selector.
- Switching sessions preserves separate message histories.
- Rename updates the selector label.
- Delete removes only the selected session.
- Markdown export still works.
- JSON export can be imported back.
- `.data/` remains ignored by Git.

## Acceptance Criteria

- Users can manage multiple local sessions from the sidebar.
- Sessions persist across Streamlit restarts.
- `.data/` is ignored by Git.
- JSON import/export works for active sessions.
- Existing chat streaming behavior still works.
- Existing Provider and runtime diagnostics remain visible.
- `pytest`, `compileall`, and `ruff check` all pass before commit and push.
