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

#### Found in use: the answer is markdown, and the page was drawing it as prose

A model writes headings, lists and tables. Rendered as one paragraph they run together
into a wall nobody reads, so the page renders markdown as the other shell does —
`markdown-it` beside its `markdown-it-py` — and substitutes the citations into it.

- [x] **(ui)** a list stays a list and `**bold**` stays bold
- [x] **(ui)** each `[n]` that names a citation becomes a button carrying it, every
      number in a run its own
- [x] **(ui)** a number citing nothing stays the text it was written as
- [x] **(ui)** a bracketed number inside code — inline or fenced — is left alone, and so
      is one inside a tag's attributes
- [x] **(ui)** a document cannot smuggle markup into the page: raw HTML is escaped
- [x] **(ui)** an answer fetches nothing — images are disabled, so a document cannot make
      the reader's browser call out

The conversation reads as a chat: what you asked is a bubble on your side, what cora
answered is the page's own text under its name, so a table or a cited passage keeps the
full column.

- [x] **(ui)** the question is on the page while the answer is still being written, with
      *Working…* under cora's name where the answer will be — asked and unanswered is a
      turn in the thread, not a question that vanished into the composer
- [x] the streaming test waits for the model to be inside `complete` rather than asking
      whether it has got there yet, and the run's deadline sits inside the model's own
      patience — a batched turn has to fail on that deadline rather than be rescued by
      the model giving up and finishing anyway

#### Found in use: the tail of an answer was read through the composer

The composer floats, so the conversation has to leave it room and follow what just
happened; otherwise the last lines of a long answer sit under the input.

- [x] **(ui)** the column reserves the composer's height, and the newest turn scrolls
      itself into view when it is asked and again when it is answered

The answer itself still arrives whole. Streaming it token by token means a streaming
path through `ChatModel`, the OpenRouter adapter, `ModelStep` and `Agent.answer` — the
contract and the engine, which this story does not touch. Left as it is: the plan
streams, so the page is never silent while the answer is written.

#### Found in use: a document in the rail opens where the mockup opens it

The mockup's `pick()` puts a document in the SOURCE panel; the rail was inert. What the
page can open is what the conversation has cited: a citation carries the upload its span
was measured in, and a filename carries nothing that reads text back.

- [x] **(ui)** a document the answer cited opens in the source panel when it is clicked
      in the rail, the panel selected and the passage marked
- [x] **(ui)** a document nothing has cited is listed and inert, saying why rather than
      offering a click that could not be answered
- [x] the source panel takes a document and every passage cited in it, so two citations
      in one file are two marks in one view — the citation popup shares the renderer
      with a span of its own
- [x] **(ui)** what is marked is what *this* answer rested on: a document cited three
      turns ago does not accumulate marks until most of it is highlighted, and an answer
      that cites nothing leaves the panel on the document last read, saying so
- [x] **(ui)** a document cited in an earlier turn still opens — what makes it readable
      is the upload any citation in the conversation names, which is a different
      question from what this answer marked in it

#### Found by the branch review (`ai-code-reviewer`, third pass)

The markdown surface resisted every injection the reviewer could construct, and the
streaming test held under load. What it found instead was a defect in the newest work
and three more ticks resting on nothing.

- [x] **(ui)** the document is rendered exactly once whatever its passages do: chunks
      overlap by `DEFAULT_OVERLAP`, so two adjacent cited chunks shared their edges and
      the panel drew a corrupted copy of the reader's own document — overlapping
      citations are one mark over what they jointly cover
- [x] **(ui)** an answer lands on the turn that asked it and on no other: a conversation
      reopened mid-turn replaces the thread wholesale, and "the last entry" was then
      somebody else's — the reopened conversation lost its last turn to an answer
      computed on a thread the reader had left
- [x] **(ui)** a run standing on its own inside a fence, and inline code that is nothing
      else, are left alone — the previous test used `rows[1]`, which the citation rule
      excludes anyway, so it passed without the code-skipping it claimed to cover
- [x] **(ui)** the answer replaces the turn that was waiting rather than following it
- [x] **(ui)** the conversation follows what just happened, answered *or* failed — a
      failure lands in place, changing neither the count of turns nor any answer, so
      nothing followed it down and it read as nothing having happened
- [x] **(ui)** a citation wrapped in a link the model wrote opens the passage and not
      the link; a link in an answer opens away from the page and carries nothing back
- [x] the page resolves a citation by the domain's own rule — the two are written in
      two languages, and nothing but this could say when they stopped agreeing

An answer is parsed once per turn rather than once per keystroke, and the stale
`@types/markdown-it` is gone.

- [x] **(ui)** a passage whose text was never kept says so rather than drawing an empty
      page — a citation carries the upload its span was measured in, and an index
      written before cora kept any text names none
- [x] **(ui)** with nothing opened the source panel says what it is for

#### Found by the branch review (`ai-code-reviewer`, fourth pass)

Six of the seven previous fixes killed their mutants. The seventh, and two defects this
round introduced, are below — and one finding is not about this story at all: a change
to the application's default model reached `main`'s neighbour by riding in on a blanket
`git add`, contradicting the README and the module's own docstring.

- [x] the default model is the one the README names, and a test says so — the constant
      reaches anyone who runs cora without naming a model, so it is a documented fact
      rather than a value to drift
- [x] **(ui)** the panels an answer steers are steered only for the conversation the
      reader is still in: the reopen guard had been applied to the thread and not to the
      document beside it, so an abandoned turn put its document in the source panel and
      had it report that its text was never kept
- [x] **(ui)** a passage whose text was never kept says so wherever it is opened — the
      reason moved next to `usePassage`, so the popup that `[1]` opens no longer draws a
      title over an empty page while the rail's panel explains itself
- [x] **(ui)** passages arrive in citation order, not document order: `[1]` can sit
      later in the file than `[2]`, and merging without ordering first drops every
      passage that precedes the one seen first — the panel counted two and marked one
- [x] **(ui)** a document that cannot be opened says why on the page rather than in a
      `title` on a disabled control, which is out of the accessibility tree

The page's own tier performs no navigation and dials no host: the click whose default
action this suite asserts about is one it must never carry out.

#### Found by the branch review (`ai-code-reviewer`, fifth pass)

Every fourth-pass fix killed its mutant. What was left was the guard itself: closed for
the ordinary case and open for the one it was written for.

- [x] **(ui)** the reply is dropped when the reader has moved on *in the same task batch
      as the reopen* — `setThread` schedules a render, so a ref assigned while rendering
      still names the old thread to anything that runs before that render lands, and two
      responses arriving in one batch is ordinary. The ref is written where the thread
      changes
- [x] **(ui)** a document that names no upload at all says why, as one naming an empty
      string already did — the panel drew a title over an empty body
- [x] **(ui)** the note explaining the greyed documents goes when there are none
- [x] **(ui)** the live plan belongs to the conversation its steps were taken in; the
      composer stays disabled until the turn ends either way, because cora answers one
      question at a time

The page's build runs in CI: a broken asset import type-checks and unit-tests clean, and
the build's output is what the server serves. The default-model test reads the README
from the repository root rather than the working directory.

#### Found by the branch review (`ai-code-reviewer`, sixth pass)

The guard on the live plan was ticked on a test that could not reach it — both steps
were already on the wire before the reopen — and stopping the growth was only half the
criterion: what the abandoned turn had already drawn stayed on the panel whose footer
says these are the steps for what is on screen.

- [x] **(ui)** a conversation shows its own plan, not the plan of a turn left behind:
      the second step is held so the reopen falls between two steps, and neither the
      step that follows it nor the step that preceded it belongs to the panel afterwards
- [x] what is drawn and what is in flight are two values: one said both, so clearing the
      panel on a reopen would have re-enabled a composer whose request is still running
- [x] **(ui)** the answer stream's body is released once the turn has arrived — the turn
      is the last thing on the wire, so the reader returns at it holding a body nobody
      will read again

Left as follow-up, deliberately: a turn carries no `AbortSignal`, so a request the
server accepts and never answers keeps the composer disabled until the page is
reloaded. Cancelling on a reopen would also decide what leaving a conversation *means*
for the turn still running in it — a decision worth taking on its own, not inside a
review fix.

#### Found by the branch review (`ai-code-reviewer`, seventh pass)

Scoped to the source, and to this frontend: the same overclaim the page's citation rule
makes is made by the core docstring it mirrors, and that wording is left where it is.

- [x] **(ui)** the text a passage is measured in and the passage marked in it come from
      one citation set — two uploads can carry one filename, so the panel opened the
      first upload the conversation ever cited and drew the newest turn's offsets in it
- [x] **(ui)** a question in flight does not un-cite the answer still on screen: the
      pending entry carries no citations, so the highlights went and the count line read
      "not cited in this answer" about an answer that cites two passages
- [x] an upload past the ingestion cap is refused before it is read, not spooled whole
      and materialised in memory and measured after
- [x] a question with no text is refused with the sentence the endpoint already carries,
      rather than answered — a blank question spends a turn and checkpoints it under a
      blank thread
- [x] `CORA_PORT` that is not a number says so the way every other numeric setting does,
      and a port below 1 is refused rather than handed to the server
- [x] a built-in tool's origin does not call a memory write "core retrieval" — the
      reserved list holds two names and only one of them searches
- [x] the page's citation rule claims only what it keeps: a number written inside code is
      resolved by the server and drawn as text, so the clickable-and-load-bearing claim
      is narrowed to the rule the two sides actually share (wording, no test)

#### Found by the branch review (`ai-code-reviewer`, eighth pass)

Two of the seventh pass's own fixes were half-closed: the panel spoke for a turn that
failed as if it were an answer, and the ceiling's test pinned the *order* of the guard
only because a malformed body made the parser raise. Core is in scope this time, so the
private helper the port borrowed gets a name of its own.

- [x] a malformed multipart upload is refused with a sentence under a 4xx, not a 500
      carrying `Internal Server Error` — the page reads a non-JSON body as "cora could
      not be reached", which is the one thing that is false when cora answered
- [x] the upload ceiling is asserted on the reading, not on the reply: a `receive` that
      fails the test if it is ever called, so the guard cannot move after the parse
- [x] `/api/ask` bounds its body like the endpoint next door, under one rule rather than
      one and a half
- [x] **(ui)** a turn that *failed* does not un-cite the answer still on screen — the
      failure branch carries no `pending` flag, so half the criterion the seventh pass
      ticked was still open
- [x] **(ui)** an answer returning to a conversation the reader left and came back to is
      not dropped: the thread guard passes while the entry it belongs to was renumbered
      by the reopen, so the turn lands nowhere
- [x] a mistyped setting reaches the operator as the sentence it was raised with, not as
      a traceback whose last line happens to be that sentence
- [x] the number every setting is parsed through has a public name: a frontend borrowing
      `config`'s private helper breaks on an ordinary rename, and no gate can see it
- [x] a built-in that is not the search tool is what proves the label, on its own: the
      new test could not fail unless the one above it already had
- [x] the toolkit a frontend is allowed is the one its manifest buys: the allow-list is
      written by hand, so adding a name to it was the cheapest way past the rule it
      enforces — now it costs a declared dependency, which ships in the metadata

#### Found by the branch review (`ai-code-reviewer`, ninth pass)

The eighth pass's own two fixes, again half-closed: the loader it added carried none of
the guard the one beside it had, and the turn it made *land* was still wiped off the page
while it ran. Two of its checklist items were ticked on tests that hold for any value of
what they pin.

- [x] **(ui)** a conversation that loads late does not overwrite the one the reader is in
      — and the one that arrives is the one they asked for last, not the one the server
      was slower about
- [x] **(ui)** the turn in flight belongs to the conversation it was asked in, not to the
      list of turns the store has: leaving that conversation and returning showed a
      thread where nothing was asked, no plan, and a composer that could not be typed in
- [x] a question of the length the engine allows is not refused by the shell that carries
      it: both ceiling tests were built *from* the constant, so they held for any value
      of it — including one that refuses every full-length question
- [x] nothing is built before the settings are read: the sentence, the exit code and the
      absent traceback all hold whichever order it happens in, so the order is asserted
      by a `build` that fails the test if it is called
- [x] a refusal keeps the headers it was raised with — a 405 without `Allow` is one the
      client cannot act on — and a status that forbids a body is given none
- [x] a body the form parser cannot read is refused as a sentence whichever way it failed:
      `MultipartParseError` has siblings, and they were still leaving a plain-text 500
