## Why

One conversation carries two names: the store is `Conversations`, what it lists is a
`Session`, and the reader meets both on the page.

## What Changes

- The list row, the listing call, the API path and the panel are named for the conversation they hold
- The tab reads CONVERSATIONS, and the controls say "New conversation", "Delete conversation" and "Back to other conversations"
- **BREAKING** `/api/sessions` becomes `/api/conversations`, for every path under it
- Capability `sessions` becomes `conversations`, moved on the branch, since a delta cannot rename one
- Capability `conversation` becomes `turn`, which is what it describes, so the two do not sit a letter apart
- Capability `conversations` — the two scenarios that name SESSIONS, and one requirement for the words the page uses
- Capability `frontend` — the three requirements that name the sessions panel

## Impact

- `src/cora/domain/conversation.py`, `src/cora/ports/conversations.py`, `src/cora/adapters/sqlite_conversations.py`, `src/cora/engine/removal.py` — `Session` and `sessions()` renamed
- `frontends/react/src/cora/frontends/react/api.py`, `payloads.py` — the routes and the payload renamed
- `frontends/react/ui/src/` — the type, the calls, `SessionsPanel`, `NewSession`, the tab and every label
- `frontends/react/ui/e2e/` — the browser tests follow the words
- `tests/` — the fakes, the adapter tests, the acceptance tests, and one new guard
- `docs/assets/domain-map.svg` — regenerated, as the class it draws is renamed
- `openspec/specs/sessions/`, `openspec/specs/conversation/` — moved to `conversations/` and `turn/`
- Left alone: `thread_id`, the model's half of a conversation, named as LangGraph names it
- Left alone: the fitness plugin's `Session` and the vocab drill's session, which are sittings
- Left alone: the "session maps" the Makefile, the guards and the process docs call the turn diagrams
