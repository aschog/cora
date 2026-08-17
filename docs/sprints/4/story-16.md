# Story 16: Read the passage the answer cites

**As a** reader · **I want** to click the `[1]` in a sentence · **So that** I can read the
passage it rests on, in its own document, without leaving the conversation

> **Given** an answer citing a passage of an indexed document
> **When** I click that citation
> **Then** the document opens beside the chat, scrolled to the cited passage with it
> highlighted — and closing it returns the chat to full width

Adds `markdown-it-py` and an inline `st.components.v2` component. `st.chat_input` stays
pinned full width. The click itself is out of AppTest's reach — Phase 4 verifies it
headless.

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
