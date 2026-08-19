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

- [ ] an empty block takes the whole of the HTML it is given
- [ ] text that grew is the same text node afterwards, carrying the longer text
- [ ] a block the reader has already read is untouched by the piece that follows it —
      same element, same text node
- [ ] a paragraph that turns out to be something else — a list forming, a fence
      opening — is replaced, because the tag is what a node is
- [ ] an attribute that appeared is set and one that went is removed, so a `[1]` becoming
      a citation button does not need the block rebuilt
- [ ] blocks the new HTML no longer has are removed — an answer restarted after an aside
      leaves nothing of the one before it
- [ ] over a whole answer arriving piece by piece, the block ends up exactly as one parse
      of the finished answer would have drawn it

#### The reader keeps their selection (`ui/src/components/Answer.tsx`) **(ui)**

- [ ] the paragraph the reader has read is the same node after three more pieces land
- [ ] the citation buttons still open their passage once the turn lands, drawn through
      the patch rather than by React
- [ ] an answer replaced wholesale — the error taking its place — draws the error and
      keeps none of the answer

#### An upload says what it did (`ui/src/App.tsx`) **(ui)**

- [ ] a file already indexed is reported as already in the knowledge base, by name
- [ ] a file that was indexed is reported as added, with how many passages it became
- [ ] one passage is `1 passage`
- [ ] the notice is not drawn as trouble — the two banners are told apart by the reader
- [ ] an upload that fails still says so, and clears the notice the last one left
- [ ] a notice stands until the next upload has something to say — a refresh going
      through does not take it away

#### A sink's failure is the sink's (`adapters/openrouter_chat_model.py`)

- [ ] a sink that raises while the stream runs raises out of `complete` as itself, not as
      `LlmError`
- [ ] a provider failure part-way through a stream is still categorised, and the pieces
      already handed on are not taken back

#### The test says what it tests (`tests/cora/adapters/test_langgraph_runner.py`)

- [ ] two runs of one runner that overlap in time each write only their own pieces — the
      claim the name makes, which two sequential runs cannot observe

#### Outer functional tests

- [ ] **(ui)** a reader who has selected a sentence of an answer being written still has
      it selected when the answer is finished
- [ ] **(ui)** uploading the same file twice says `added` and then `already`, from the
      counts the route already answers with
