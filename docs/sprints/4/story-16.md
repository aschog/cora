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

- [ ] `Citation` carries number, document, start and end; `Source` is gone
- [ ] `build_context_block` numbers one citation per hit — two passages of one document
      are `[1]` and `[2]`
- [ ] a passage already registered keeps its number when the same span comes back
- [ ] numbering continues past the citations already known
- [ ] the block still renders `[n] document: text`, one line per hit
- [ ] `cited(text, citations)` returns only cited passages, ascending
- [ ] `ChatResult.citations` are the cited passages, resolved against those registered
- [ ] **(int)** a citation survives a second turn on one thread — the checkpoint allowlist
      names it where it named `Source`

#### The stored document (`ports/documents.py`, `adapters/sqlite_documents.py`)

- [ ] `keep` then `read` returns the text unchanged, across a reopened database
- [ ] `read` of a name never kept returns `None`
- [ ] keeping the same name twice leaves the later text
- [ ] a `sqlite3.Error` surfaces as an `AdapterError`, not a raw driver error
- [ ] the parent directory is created if missing
- [ ] `build` wires the store at `CORA_DOCUMENTS_PATH`, and a blank value reads as unset
      like every other path setting

#### Ingest keeps what the offsets point at (`ingestion.py`, `knowledge_base.py`)

- [ ] `ingest` returns the cleaned text alongside the chunks
- [ ] `add_file` keeps that text under the document's name
- [ ] **the invariant**: for every chunk of an ingested file,
      `read(name)[chunk.offset : chunk.offset + len(chunk.text)] == chunk.text`, over a
      document long enough to chunk with overlap
- [ ] a file already indexed keeps nothing further and still returns 0 chunks
- [ ] a document that fails to ingest keeps nothing
- [ ] `KnowledgeBase.text(name)` returns what was kept, `None` for an unknown name

#### Rendering (`formatting.py`, pure)

- [ ] `answer_html` renders markdown — a bullet list stays a list, `**bold**` stays bold
- [ ] each `[n]` that resolves becomes a button carrying `data-cite="n"`
- [ ] an `[n]` with no registered citation stays literal text
- [ ] a bracketed number inside a fenced code block is left alone
- [ ] `document_html` escapes the document — `<script>` in a document renders as text
- [ ] it wraps `[start:end]` in a mark carrying the anchor id, and marks nothing else
- [ ] a span running past the end of the text marks to the end rather than raising

#### The pane (`viewer.py`, `chat.py`)

- [ ] with no citation open the chat renders full width and no document heading appears
- [ ] opening a citation renders that document's name as a heading beside the chat
- [ ] the pane shows the document the citation names, not another
- [ ] the close button clears the open citation and the heading goes with it
- [ ] a citation from an earlier answer in the thread still opens — the registry spans
      messages
- [ ] a citation whose document was never kept says so instead of rendering an empty pane
- [ ] an `AdapterError` reading the document is reported in the pane and costs the chat
      nothing
- [ ] the Sources expander lists one line per cited passage, not one per document

#### Outer functional test

- [ ] **(int)** `xfail(strict=True)` until the list is done: a scripted turn cites a
      passage, opening it shows that document with the cited text marked, and closing it
      restores the full-width chat
