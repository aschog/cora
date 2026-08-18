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

- [x] `cora-frontend-react` resolves in the workspace and imports `cora`, and the
      existing purity guard still finds no core module importing a frontend

#### Payloads (`payloads.py`, pure)

- [x] a `Citation` renders as its number, document, span and upload — the upload is what
      the page reads a passage back with
- [x] a `ToolUse` step renders its summary, detail and failed flag; a `ModelDecision`
      renders the same three keys, so the page draws one kind of step
- [x] a `ChatResult` renders as answer, citations and trace
- [x] a `Turn` renders as its question and that result, so a reopened conversation
      redraws from the same shape a fresh answer arrives in
- [x] a `Fact` renders as key and text; a `Session` as thread id and opening question

#### Documents (`api.py`)

- [x] `GET /api/documents` lists what the knowledge base has indexed
- [x] `POST /api/documents` ingests the upload and reports the chunks it cut
- [x] a file already indexed reports no chunks rather than failing
- [x] a `CoreError` on ingest answers with its `user_message` and a 4xx, never a
      traceback, and leaves nothing indexed
- [x] `GET /api/uploads/{upload}` returns the text that upload was kept as
- [x] an upload never kept answers 404, so a passage that cannot be opened says so

#### Asking, as it happens (`api.py`)

- [x] `POST /api/ask` streams `step` events in the order the agent took them, then one
      `turn` event carrying the answer, its citations and its trace
- [x] the stream's `turn` event is the last thing on the wire — a client that stops
      reading at it has the whole answer
- [x] the thread id the client sends is the thread the agent answers on, so a follow-up
      continues the conversation rather than opening one
- [x] a `CoreError` mid-turn arrives as an `error` event carrying `user_message`, after
      the steps already taken, and the stream closes
- [x] a turn that fails before any step still closes the stream with that error, rather
      than hanging the page on an open connection

#### Conversations and memory (`api.py`)

- [x] `GET /api/sessions` lists the stored sessions newest first
- [x] `GET /api/sessions/{thread_id}` returns that thread's turns, oldest first
- [x] a thread never recorded answers with an empty list rather than 404 — an unopened
      conversation is empty, not missing
- [x] `GET /api/memory` lists the facts oldest first
- [x] `DELETE /api/memory/{key}` forgets one; `DELETE /api/memory` clears every one
- [x] a memory store that cannot be read answers with its `user_message` and costs the
      rest of the page nothing
- [x] an app assembled without memory or conversations answers both as empty rather than
      failing — the panels are absent, not broken

#### What is loaded (`api.py`)

- [x] `GET /api/plugins` names the plugin modules the deployment configured
- [x] with no plugins configured it answers empty, and the page says bare cora

#### Serving the page (`api.py`)

- [x] a built `ui/dist` is served at `/`, so one process is the whole app
- [x] with no build present the API still answers — a missing UI is a dev machine, not a
      broken deployment

#### The page, once (`ui/src/App.test.tsx`)

- [x] **(ui)** the happy path: against a stubbed `fetch` serving one document, one
      plugin and an answer stream of two steps and a turn, asking a question fills the
      plan with those steps, renders the answer, and draws its `[1]` as a button

#### Outer functional test

- [x] **(int)** `xfail(strict=True)` until the list is done: over an assembled app, a
      document is uploaded, a question asked, its steps stream, the answer cites that
      document, the cited passage reads back from its upload, and the conversation is
      listed and reopens with that turn in it

#### Found by the branch review (`ai-code-reviewer`, PR #36)

Three ticked items rested on tests that were shown, by mutation, not to bite: batching
every event and sending them at the end passed the whole suite, and the page's one spec
survived both stubbing `onStep` to nothing and dropping the stream buffer.

- [x] a step reaches the page while the model is still inside `complete` — driven
      against the ASGI app itself, because `TestClient` buffers a response before it
      hands it over, so nothing seen through it can tell a stream from a batch
- [x] **(ui)** the streamed steps say what the finished turn does not, and the turn is
      withheld until the test lets it go — so a plan drawn from the turn's own trace
      cannot satisfy the assertion
- [x] **(ui)** a frame split across two reads still arrives, so a client that drops what
      it buffered loses a step the assertion needs
- [x] **(ui)** a `DELETE` that answers 503 rejects rather than resolving — the empty-body
      parse is not caught by swallowing every failure with it
- [x] a turn broken in a way nobody modelled ends the stream with an `error` event, its
      message generic and its traceback in the log — an ended stream reads as a cut
      connection and invites the same question again
- [x] a body that is not a question is refused with a message and a 400, as a missing
      file already was
- [x] the events cross to the response through the event loop, not through a pool thread
      parked in `Queue.get`: that thread is one of the pool every other endpoint shares,
      and it cannot be cancelled when the reader closes the tab
- [x] a frontend may import only the toolkit its own shell was given — the allow-list is
      keyed by portion, so the widget shell reaching for the HTTP server fails, which is
      what `big-picture.md` already claimed
- [x] every frontend declares its toolkit, so a third shell inherits nothing
- [x] `DEFAULT_UI` lands on this repository's `ui/`, and `CORA_UI_PATH` names the build
      for a deployment installed from a wheel, where nothing sits beside the package
- [x] **(ui)** a panel that could not be read says so, and stops saying it once a later
      load goes through

#### Found in use: the page took the mockup's second shape

`docs/cora_mockup.html` was redrawn — glass rails over a lit ground, the four panels as
pills, the plugin badge a disclosure, and a composer that floats over the conversation
rather than sitting after it. Both rails fold away, which is what the two icons in the
header do.

- [x] a step says where its work came from — `search_documents` and `remember` are cora's
      own, anything else on offer came from the loaded plugin, which is the origin line
      the plan panel draws
- [x] a step that called no tool claims no origin, and a kind the engine adds next still
      renders from the base class alone
- [x] **(ui)** the badge names the loaded shell and the disclosure names the module it
      was loaded from — there is no swap to offer, because plugins bind at assembly

The page serves its own copy of Source Serif 4: an app whose pitch is *your* documents
should not call a third party to draw them.

#### Found by the branch review (`ai-code-reviewer`, second pass)

Every finding of the first pass was confirmed closed by re-running its mutations. Two
survived new ones, and one duplication was found that no test could have caught.

- [x] the traceback of an unmodelled failure is in the log — the screen is spared it, so
      the log is the only place it exists, and deleting the line failed nothing
- [x] the stream says `Cache-Control: no-cache` and `X-Accel-Buffering: no` — a proxy
      that buffers delivers every step at the end, which is the shape the endpoint
      exists not to have, and no test read the headers
- [x] a built-in the engine gains is not reported as a plugin's: the origin line reads
      `RESERVED_TOOL_NAMES`, the list a plugin's tool names are already refused against,
      rather than a copy of the two names it holds today
- [x] **(ui)** each rail folds away and comes back, and its toggle says which it is —
      the collapse shipped with no cover at all
- [x] forgetting where nothing is kept is done rather than missing, so the two `DELETE`s
      read like every other panel with no store behind it
- [x] **(ui)** the badge is loaded with the panels rather than beside them — on its own
      it raced the banner, and a page that could not find out which plugin is loaded
      would say `bare cora` and then clear the only warning that it was guessing

`CORA_UI_PATH`, `CORA_HOST` and `CORA_PORT` are in the README, which the previous pass
claimed and did not do; so is the React tier, which the gates section had never named.
