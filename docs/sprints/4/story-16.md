# Story 16: Read the passage the answer cites

**As a** reader · **I want** to click the `[1]` in a sentence · **So that** I can read the
passage it rests on, in its own document, without leaving the conversation

> **Given** an answer citing a passage of an indexed document
> **When** I click that citation
> **Then** the document opens over the chat, scrolled to the cited passage with it
> highlighted — and closing it returns me to the conversation

Adds `markdown-it-py` and an inline `st.components.v2` component. The click itself is out
of AppTest's reach — Phase 4 verifies it headless.

The story grew a second half in use: the page took the shape of `docs/cora_mockup.html`,
which put the passage in a rail beside the conversation as well as in the popup, and the
conversations that rail lists have to outlive the process.

## Test list

**Tiers:** unit unless marked — **(int)** integration.

#### A citation is a passage (`citations.py`)

- [x] `Citation` carries number, document, start and end; `Source` is gone
- [x] `build_context_block` numbers one citation per hit — two passages of one document
      are `[1]` and `[2]`
- [x] a passage already registered keeps its number when the same span comes back
- [x] numbering continues past the citations already known
- [x] the block still renders `[n] document: text`, one line per hit
- [x] `cited(text, citations)` returns only cited passages, ascending
- [x] `ChatResult.citations` are the cited passages, resolved against those registered
- [x] **(int)** a citation survives a second turn on one thread — the checkpoint allowlist
      names it where it named `Source`

#### The stored document (`ports/documents.py`, `adapters/sqlite_documents.py`)

- [x] `keep` then `read` returns the text unchanged, across a reopened database
- [x] `read` of a name never kept returns `None`
- [x] keeping the same name twice leaves the later text
- [x] a `sqlite3.Error` surfaces as an `AdapterError`, not a raw driver error
- [x] the parent directory is created if missing
- [x] `build` wires the store at `CORA_DOCUMENTS_PATH`, and a blank value reads as unset
      like every other path setting

#### Ingest keeps what the offsets point at (`ingestion.py`, `knowledge_base.py`)

- [x] `ingest` returns the cleaned text alongside the chunks
- [x] `add_file` keeps that text under the document's name
- [x] **the invariant**: for every chunk of an ingested file,
      `read(name)[chunk.offset : chunk.offset + len(chunk.text)] == chunk.text`, over a
      document long enough to chunk with overlap
- [x] a file already indexed keeps nothing further and still returns 0 chunks
- [x] a document that fails to ingest keeps nothing
- [x] `KnowledgeBase.text(upload)` returns what was kept, `None` for an unknown upload

#### Rendering (`formatting.py`, pure)

- [x] `answer_html` renders markdown — a bullet list stays a list, `**bold**` stays bold
- [x] each `[n]` that resolves becomes a button carrying `data-cite="n"`
- [x] an `[n]` with no registered citation stays literal text
- [x] a bracketed number inside a fenced code block is left alone
- [x] `document_html` escapes the document — `<script>` in a document renders as text
- [x] it wraps `[start:end]` in a mark carrying the anchor id, and marks nothing else
- [x] a span running past the end of the text marks to the end rather than raising

#### The pane (`viewer.py`, `chat.py`)

- [x] with no citation open the chat renders full width and no document heading appears
- [x] opening a citation renders that document's name as a heading beside the chat
- [x] the pane shows the document the citation names, not another
- [x] the close button clears the open citation and the heading goes with it
- [x] a citation from an earlier answer in the thread still opens — the registry spans
      messages
- [x] a citation whose document was never kept says so instead of rendering an empty pane
- [x] an `AdapterError` reading the document is reported in the pane and costs the chat
      nothing
- [x] ~~the Sources expander lists one line per cited passage, not one per document~~ —
      built, then removed; see *the numbers in the answer are the only way in* below

#### Outer functional test

- [x] **(int)** `xfail(strict=True)` until the list is done: a scripted turn cites a
      passage, opening it shows that document with the cited text marked, and closing it
      restores the full-width chat

#### Found by the branch review (`ai-code-reviewer`, PR #35)

- [x] a passage found in one upload still reads that upload's text after the same
      filename is uploaded again with other text in it — the kept text is keyed by the
      upload, and a hit carries the upload it was cut from
- [x] a document whose text cannot be kept is never left searchable: `keep` is written
      before the index will hand the passage out
- [x] every number in a run — `[1][2]` — becomes its own button, the rule `cited_numbers`
      already read by
- [x] a bracketed number inside a tag is left alone; substitution runs over the text of
      the rendered HTML, not its attributes
- [x] an image in an answer fetches nothing — the renderer has images disabled, so a
      document cannot make the reader's browser call out
- [x] the live-model citation check reads the answer, not the Sources panel, so it can
      fail again
- [x] a passage whose text was never kept says so under its document's heading, told
      apart from a number belonging to no answer in the thread
- [x] closing the pane gives the conversation its full width back — the column split
      goes, not just the pane's contents
- [x] a citation carries the upload its span was measured in, and one span of two
      uploads is two citations — the domain half of the keying, pinned by a mutation
- [x] uploading a file again repairs text an index never had, rather than leaving its
      passages unopenable for good

#### Found in use: a plan-sized answer never finishes (`config.py`, `openrouter_chat_model.py`)

A reasoning model spends its output budget thinking before it writes a word, so the two
numbers sized for `gpt-4o-mini` — 2048 tokens, 20 seconds — cannot fit a training plan
under `gpt-5-mini`. The deployment that names the model names its budgets.

- [x] `Config.from_env` reads `CORA_MAX_OUTPUT_TOKENS`, defaulting to room for a
      reasoning model's thinking *and* a plan-sized answer
- [x] `Config.from_env` reads `CORA_REQUEST_TIMEOUT`, defaulting to a deadline such an
      answer arrives within
- [x] both refuse a non-integer, a blank and a value below their lowest useful one, like
      every other count
- [x] `OpenRouterChatModel` builds its client with the budgets it was handed, not with
      module constants
- [x] `build` hands the config's budgets to the model, so setting them in the environment
      reaches the client

#### How hard the model thinks is the deployment's dial too (`config.py`, `openrouter_chat_model.py`)

Measured on the same question: at `medium` — the provider's default — `gpt-5-mini` takes
32-61s a turn, at `low` 22-25s, and it searches the documents and cites either way. The
dial belongs beside the budgets it spends.

- [x] `Config.from_env` reads `CORA_REASONING_EFFORT`, defaulting to the setting measured
      to answer fastest without costing the citations
- [x] an effort no provider defines is refused at startup rather than sent
- [x] `OpenRouterChatModel` asks for the effort it was handed in the request body
- [x] `build` hands the configured effort to the model

#### Found in use: the numbers in the answer are the only way in (`chat.py`, `viewer.py`)

The Sources expander listed what the buttons already open, under every answer, and the
mark wore the theme's primary — the same colour the buttons wear, so the passage and the
click that opened it read as unrelated.

- [x] an answer carrying citations renders no Sources expander
- [x] `numbered_citations` goes with the panel it fed
- [x] the cited passage is marked in the citation colour rather than filled with the
      theme's primary on the theme's background
- [x] a citation button wears that same colour, so click and highlight match
- [x] the live tier reads the answer and its trace for proof the documents were reached,
      having lost the panel it read before

#### Found by the branch review (`ai-code-reviewer`, second pass)

- [x] a citation the reader can click is told apart from a bracketed number that resolved
      to nothing — `[1]` written against no registered passage is not proof of a citation,
      and the live tier's positive checks read the clickable one
- [x] `build` opens no store outside the paths it was configured with: the test that
      proves a fresh install is empty says where all three of its stores live
- [x] `_expander` goes with the panel it drew, as `numbered_citations` already did
- [x] the architecture table names what the shell draws today, the sources box having
      gone

#### Found by the branch review (`ai-code-reviewer`, third pass)

- [x] the citations a helper reports are the newest answer's, not every answer's on the
      page — the scoping its predecessor carried, back and pinned
- [x] a resolved number and one glued to a word sit in the same answer, and only the
      resolved one is clickable — the distinction the previous test claimed and never drew
- [x] a turn that failed reports the error the page is showing, rather than raising while
      it builds the message that would have said so
- [x] what counts as a citation run is the domain's rule, imported by the renderer rather
      than restated beside it — a mutation to the rule fails the renderer's tests too
- [x] `build` writes its debug log where the deployment says, `CORA_LOG_PATH` naming it
      like every other path

#### Found by the branch review (`ai-code-reviewer`, fourth pass)

Three rounds of patching page-wide readers produced three rounds of findings: a helper
that takes the last of every answer on the page is guessing at "this turn", and a thread
redraws every turn on every rerun. The thread itself is what knows where a turn ends.

- [x] a turn that failed after an earlier one answered reports neither that earlier
      answer nor its citations — the newest *turn*, not the newest element of a kind
- [x] a check that reads the answer of a turn that gave none fails loudly, naming what
      the page said instead: an error read as an answer is how `assert X not in answer`
      passes while the model never answered
- [x] the error a failed turn reports is the chat's, not any error the page happens to
      show — a sidebar that cannot reach the memory store is not this turn's answer
- [x] `build` writes its debug log where the config says: a mutation to the wiring fails,
      and the test that switches debugging on writes nothing into the working directory

#### Found in use: the passage pops up over the chat (`chat.py`, `viewer.py`)

Splitting the page was the wrong shape whichever way the split ran: a third is a document
read in fragments, two thirds costs the conversation its line, and a filename set as a
page heading broke over three lines either way. A cited passage is something you open,
read and dismiss — `@st.dialog` is that, and the chat keeps the whole page while it is
open. The column split goes, and with it the wide/centered switch it needed.

A dialog's contents land in AppTest's event container rather than `at.main`, which is why
the shared reader is the first item: nothing else can be seen until it looks there.

- [x] **(int)** `mounted_html` finds a component drawn inside a dialog, and the pane
      opens in one — the page keeps no column split behind it
- [x] **(int)** the dialog is titled with the document's name, the page-wide heading gone
- [x] **(int)** the dialog is dismissible and a dismissal is handled — Streamlit stamps an
      id only when one is, and a dismissal nothing handled would reopen the popup for
      ever. AppTest cannot dismiss a dialog, so what the handler *does* rests on the
      Close button's test, which drives the same `close_citation`
- [x] **(int)** a passage never kept and a number belonging to no answer are told apart by
      the popup's title, now the heading that told them apart has gone
- [x] ~~the chat keeps its full width and its input while a document is open~~ — no test
      of its own to write: the popup's own test asserts the page keeps no split, and the
      chat input is asserted where the document opens

The `[1]` in an answer is a component's button, so the click that opens a popup — and the
Escape that dismisses it — are both out of AppTest's reach. Phase 4 drives them.

#### Found in use: the popup's own chrome is enough (`viewer.py`)

A large dialog is most of the screen for a document that does not need it, and a Close
button under the title repeats the cross the title bar already carries. Losing that button
costs the tests the one way they had to close a popup headlessly, so what it drove is
pinned where it can be: on `close_citation` itself.

- [x] **(int)** the popup is small, not large
- [x] **(int)** nothing inside the popup offers a second way out — the title bar's cross
      is the way out
- [x] **(int)** `close_citation` clears the open citation, and a citation cleared takes
      the popup and its passage with it

#### Found in use: the page is three rails, not one column (`chat.py`, `streamlit_app.py`)

`docs/cora_mockup.html` is the shape being built to: documents down the left, the
conversation in the middle, and a rail on the right carrying what the answer rests on.
Native Streamlit throughout — the sidebar is the left rail, `st.columns` splits the
rest, `st.tabs` is the right one. `st.chat_message` stays: who said what is the one
thing typography alone would not carry. The page is laid out wide, which AppTest cannot
see — Phase 4 checks it.

- [x] the conversation and the rail split the page, the conversation the wider of the two
- [x] the question is asked inside the conversation's column rather than pinned across
      the page
- [x] the header names the app and what it is, above both rails
- [x] ~~the sidebar holds documents alone, the memory panel having moved to the rail~~ —
      the same increment as the rail's memory panel below, and pinned there
- [x] ~~the rail is drawn before a turn is taken, so the first answer does not reflow
      the page~~ — nothing to see until the rail has panels; pinned below

#### Found in use: what the answer rests on is a rail (`chat.py`, `viewer.py`)

Four panels: how the answer was reached, the document it cites, the conversations before
this one, and what cora has been told to remember. The plan is today's "How I got there"
moved out of the answer it sat under — one rail showing the newest turn, rather than an
expander per message.

- [x] the rail carries four panels, named plan, source, sessions and memory
- [x] the plan panel holds each turn's steps in thread order, and no answer carries a
      panel of its own — every turn's, not the newest: a trace surviving the next
      question is already pinned, and one rail showing only the last would drop it
- [x] a turn that went wrong says so in the plan panel, the news having nowhere else to go
- [x] the steps of a turn in progress arrive in the plan panel rather than beside the
      answer being written
- [x] the source panel shows the document the open citation names, marked at the passage
- [x] with nothing yet cited the source panel says what it is for, rather than drawing
      an empty document
- [x] the source panel keeps the passage last read after its popup is dismissed —
      cleared with the popup it would be empty except while the popup covers it
- [x] the memory panel lists the facts and forgets one, the sidebar's copy gone
- [x] the four panels are drawn before a turn is taken, so the first answer does not
      reflow the page
- [x] a memory store that cannot be read reports inside its own panel and costs the
      conversation nothing

#### A conversation outlives the process (`ports/conversations.py`, `adapters/sqlite_conversations.py`)

Reopening a conversation makes the runner's docstring false twice over: the turns the
page redraws have to survive a restart, and so does what the model was told, or a
follow-up in a resumed session answers without its own history. Two stores because they
hold different things — the rendered turn, and the messages the model saw — and the
checkpointer already owns the second.

- [x] `record` then `turns` returns the turn unchanged, across a reopened database
- [x] `turns` of a thread never recorded is empty rather than raising
- [x] `sessions` lists the threads newest first, each named by the question that opened it
- [x] a recorded turn keeps its citations and its trace, so a reopened conversation is
      clickable and its plan is readable
- [x] a `sqlite3.Error` surfaces as an `AdapterError`, not a raw driver error
- [x] the parent directory is created if missing
- [x] `Agent.answer` records the turn it took, so a frontend gets history without keeping
      it itself
- [x] a turn that failed records nothing — a conversation is reopened to read what was
      answered, and there is no answer to come back to
- [x] an agent wired to no store answers as it always did
- [x] a store that cannot be written costs the turn nothing — the answer arrives and
      the conversation is simply not kept, as failing to file a note never costs an
      answer either
- [x] `Config.from_env` reads `CORA_CONVERSATIONS_PATH`, and a blank value reads as unset
      like every other path setting
- [x] `build` wires the store at that path, and still opens no store outside the paths it
      was configured with
- [x] **(int)** the runner checkpoints where the config says, so a thread resumed in a
      second process carries what the model was told
- [x] a runner told no path keeps its thread in memory, as every test of it relies on
- [x] **(int)** `build` checkpoints into the conversations file, so one file holds both
      halves of a conversation
- [x] the sessions panel lists the stored sessions, the one in progress marked
- [x] with nothing recorded the sessions panel says what will fill it
- [x] a store that cannot be read reports inside the sessions panel and costs the
      conversation nothing — listing them and opening one both
- [x] opening a session redraws its turns in the conversation
- [x] the question asked after opening a session runs on that thread rather than a new one

#### Outer functional test

- [x] **(int)** `xfail(strict=True)` until the list is done: documents in the sidebar and
      the conversation beside a four-panel rail, a turn whose plan is in the rail and
      whose citation still pops up — and that conversation listed and re-openable from a
      second process
