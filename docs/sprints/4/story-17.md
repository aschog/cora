# Story 17: The React shell is a frontend, not a mockup

**As a** reader · **I want** the React page to answer from my own documents · **So that**
the shell I like is the shell I use, not a picture of one

> **Given** cora assembled over a real store and a document indexed
> **When** I ask a question in the React page
> **Then** the plan fills as the agent works, the answer arrives citing that document,
> clicking `[1]` opens the passage, and the conversation is listed to reopen

`prototypes/cora-ui` moves to `frontends/react/ui` and stops being a prototype: a
workspace member `cora-frontend-react` joins `cora-frontend-streamlit` beside it. The
shell is a second frontend over the same `App` — no core module changes.

**Starlette, not FastAPI.** Six endpoints hand-serialising domain dataclasses; pydantic
would restate `Citation`, `TraceStep` and `Fact` for nothing. Its `TestClient` runs on
`httpx`, already a dev dependency, so the API is testable without a live port. `uvicorn`
runs it; Vite proxies `/api` in dev, and the same app mounts `ui/dist` in production.

**What the mockup draws that cora cannot say.** The plugin badge names the modules
`CORA_PLUGINS` loaded and does not offer a swap — plugins bind at assembly. A plan step
carries summary, detail and failure, so the mockup's *origin* line goes. The SOURCE
panel's per-document note prose has no source in cora and goes with it. A document opens
only when the answer cites it: a citation carries the upload its span was measured in,
and `list_sources()` returns names with no map back to an upload.

**One test covers the React side.** The browser tier was retired and nothing replaces it:
`vitest` over `happy-dom` with `@testing-library/react`, and a single happy-path spec that
mounts the page against a stubbed `fetch`. It needs node, so it runs as its own CI job
rather than joining the pre-commit hook. The client reads the answer stream with `fetch`
and a stream reader rather than `EventSource` — a question is a POST, which `EventSource`
cannot send, and a stubbed `fetch` is the whole fixture.

## Test list

**Tiers:** unit unless marked — **(int)** integration, **(ui)** vitest, run by `npm test`
in `frontends/react/ui`.

#### The package (`frontends/react/pyproject.toml`)

- [ ] `cora-frontend-react` resolves in the workspace and imports `cora`, and the
      existing purity guard still finds no core module importing a frontend

#### Payloads (`payloads.py`, pure)

- [ ] a `Citation` renders as its number, document, span and upload — the upload is what
      the page reads a passage back with
- [ ] a `ToolUse` step renders its summary, detail and failed flag; a `ModelDecision`
      renders the same three keys, so the page draws one kind of step
- [ ] a `ChatResult` renders as answer, citations and trace
- [ ] a `Turn` renders as its question and that result, so a reopened conversation
      redraws from the same shape a fresh answer arrives in
- [ ] a `Fact` renders as key and text; a `Session` as thread id and opening question

#### Documents (`api.py`)

- [ ] `GET /api/documents` lists what the knowledge base has indexed
- [ ] `POST /api/documents` ingests the upload and reports the chunks it cut
- [ ] a file already indexed reports no chunks rather than failing
- [ ] a `CoreError` on ingest answers with its `user_message` and a 4xx, never a
      traceback, and leaves nothing indexed
- [ ] `GET /api/uploads/{upload}` returns the text that upload was kept as
- [ ] an upload never kept answers 404, so a passage that cannot be opened says so

#### Asking, as it happens (`api.py`)

- [ ] `POST /api/ask` streams `step` events in the order the agent took them, then one
      `turn` event carrying the answer, its citations and its trace
- [ ] the stream's `turn` event is the last thing on the wire — a client that stops
      reading at it has the whole answer
- [ ] the thread id the client sends is the thread the agent answers on, so a follow-up
      continues the conversation rather than opening one
- [ ] a `CoreError` mid-turn arrives as an `error` event carrying `user_message`, after
      the steps already taken, and the stream closes
- [ ] a turn that fails before any step still closes the stream with that error, rather
      than hanging the page on an open connection

#### Conversations and memory (`api.py`)

- [ ] `GET /api/sessions` lists the stored sessions newest first
- [ ] `GET /api/sessions/{thread_id}` returns that thread's turns, oldest first
- [ ] a thread never recorded answers with an empty list rather than 404 — an unopened
      conversation is empty, not missing
- [ ] `GET /api/memory` lists the facts oldest first
- [ ] `DELETE /api/memory/{key}` forgets one; `DELETE /api/memory` clears every one
- [ ] a memory store that cannot be read answers with its `user_message` and costs the
      rest of the page nothing
- [ ] an app assembled without memory or conversations answers both as empty rather than
      failing — the panels are absent, not broken

#### What is loaded (`api.py`)

- [ ] `GET /api/plugins` names the plugin modules the deployment configured
- [ ] with no plugins configured it answers empty, and the page says bare cora

#### Serving the page (`api.py`)

- [ ] a built `ui/dist` is served at `/`, so one process is the whole app
- [ ] with no build present the API still answers — a missing UI is a dev machine, not a
      broken deployment

#### The page, once (`ui/src/App.test.tsx`)

- [ ] **(ui)** the happy path: against a stubbed `fetch` serving one document, one
      plugin and an answer stream of two steps and a turn, asking a question fills the
      plan with those steps, renders the answer, and draws its `[1]` as a button

#### Outer functional test

- [ ] **(int)** `xfail(strict=True)` until the list is done: over an assembled app, a
      document is uploaded, a question asked, its steps stream, the answer cites that
      document, the cited passage reads back from its upload, and the conversation is
      listed and reopens with that turn in it
