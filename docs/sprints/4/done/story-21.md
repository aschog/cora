# Story 21: The page keeps what the reader has, and a failure is called what it is

**As a** reader · **I want** the page to leave what I am reading alone and to tell me what
became of what I handed it · **So that** I can copy an answer while it is still being
written, and know whether the document I uploaded was added

> **Given** an answer being written piece by piece
> **When** I select a sentence that is already on the page
> **Then** my selection is still there after the next piece arrives

> **Given** a document already in my knowledge base
> **When** I upload the same file again
> **Then** the page tells me it is already there — rather than being silent, and rather
> than calling it a failure

> **Given** a document that is not in it yet
> **When** I upload it
> **Then** the page confirms it was added, and how much of it was indexed

Closes the *Real bugs, next* block of `manual-test-findings.md` — #19, #2, #22, #21.

Two of the four are the page: an answer's DOM is thrown away and rebuilt on every token,
so the reader's selection collapses and copying mid-stream is impossible (#19), and a
duplicate upload is answered with silence, which reads the same as success and the same as
nothing happening (#2). The other two are about naming: a failure raised by the *sink* is
reported to the reader as the model being unavailable (#22), and a test claims a property
its two sequential runs cannot observe (#21).

## Test list

**Tiers:** unit unless marked — **(int)** integration, **(ui)** vitest via `make ui-test`.

#### The rendered answer is patched, not replaced (`ui/src/patch.ts`) **(ui)**

- [x] an empty block takes the whole of the HTML it is given
- [x] text that grew is the same text node afterwards, carrying the longer text
- [x] a block the reader has already read is untouched by the piece that follows it —
      same element, same text node
- [x] a paragraph that turns out to be something else — a list forming, a fence
      opening — is replaced, because the tag is what a node is
- [x] an attribute that appeared is set and one that went is removed, so a `[1]` becoming
      a citation button does not need the block rebuilt
- [x] blocks the new HTML no longer has are removed — an answer restarted after an aside
      leaves nothing of the one before it
- [x] over a whole answer arriving piece by piece, the block ends up exactly as one parse
      of the finished answer would have drawn it

#### The reader keeps their selection (`ui/src/components/Answer.tsx`) **(ui)**

- [x] the paragraph the reader has read is the same node after three more pieces land —
      the outer test below is this test; a second one asserting it mid-stream would assert
      the same nodes twice
- [x] ~~the citation buttons still open their passage once the turn lands, drawn through
      the patch rather than by React~~ — no test to write: story 19's outer test clicks
      that button, and it now clicks one the patch drew
- [x] ~~an answer replaced wholesale — the error taking its place — draws the error and
      keeps none of the answer~~ — no test to write: *a turn that fails after writing
      shows the error in place of what was written* already covers it, and the block is
      unmounted rather than patched

#### An upload says what it did (`ui/src/App.tsx`) **(ui)**

- [x] a file already indexed is reported as already in the knowledge base, by name —
      the outer test below
- [x] a file that was indexed is reported as added, with how many passages it became —
      the outer test below
- [x] one passage is `1 passage`
- [x] the notice is not drawn as trouble — the two banners are told apart by the reader
- [x] an upload that fails still says so, and clears the notice the last one left
- [x] a notice stands until the next upload has something to say — a refresh going
      through does not take it away

#### A sink's failure is the sink's (`adapters/openrouter_chat_model.py`)

- [x] a sink that raises while the stream runs raises out of `complete` as itself, not as
      `LlmError`
- [x] ~~a provider failure part-way through a stream is still categorised, and the pieces
      already handed on are not taken back~~ — no test to write: *a stream that fails part
      way keeps the category and what was written* is that test, and it stays green because
      only the provider's own iteration is left inside the categories

#### The test says what it tests (`tests/cora/adapters/test_langgraph_runner.py`)

- [x] two runs of one runner that overlap in time each write only their own pieces — the
      claim the name makes, which two sequential runs cannot observe

#### Outer functional tests

- [x] **(ui)** a reader who has selected a sentence of an answer being written still has
      it selected when the answer is finished
- [x] **(ui)** uploading the same file twice says `added` and then `already`, from the
      counts the route already answers with

#### Found while building it

- [x] **the criterion is asserted as nodes, not as a selection.** happy-dom keeps a
      selection alive across the removal of the very nodes it was made in, where a browser
      collapses it — so a selection test would have passed before the fix. What the fix
      buys the reader is their nodes surviving, and that is what the outer test pins
- [x] the notice needed a tone of its own: the banner region drew everything with
      `.trouble`, whose magenta rule is what the page keeps for something having gone
      wrong. A duplicate upload is news
