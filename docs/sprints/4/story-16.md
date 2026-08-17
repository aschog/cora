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
- [x] the Sources expander lists one line per cited passage, not one per document

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
