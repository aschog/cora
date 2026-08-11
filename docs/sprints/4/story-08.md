# Story 8: It answers from my documents

**As a** user who uploaded documents · **I want** answers built on them ·
**So that** I get my material back, not what the model happens to know

> **Given** a question in the plugin's own subject, and documents that cover it
> **When** I ask it without ever saying "my documents"
> **Then** the answer rests on a search and cites it — while small talk is still
> answered without touching the documents

The backlog's *No grounding or scope decision* (`sprint-4-feedback.md`), found in use: cora
answered a beginner-training question from model knowledge and said so. Numbered 8 because
the spec's story numbers are referenced elsewhere; it merges with story 2.

## Test list

**Tiers:** unit unless marked — **(int)** integration, **(llm)** live model.

#### Routing reads the reply, not the answer key *(migrated)*

- [x] a tool-calling reply still routes to `tools`, and still raises `ToolLoopLimitError` at
      the budget — the router reads the last message's `tool_calls`, so a stale `answer` from
      an earlier round can no longer end a run
- [x] a final reply routes to `done` when nothing asks for grounding

#### The gate

- [x] a final reply with no tool behind it routes to `ground` when the plugin asks for it
- [x] a final reply that followed a search routes to `done`
- [x] an answer a plugin's own tool worked for routes to `done` — a calculation is as good
      a ground as a document, and nudging it would retrieve for arithmetic *(review)*
- [x] a failure in the gate's extra round returns the answer it was second-guessing, while
      a failure once that round has landed still travels out — the nudge remembers the round
      it interrupted, and a stale answer never collects citations from a search it never saw
      *(review, twice)*
- [x] the round-budget apology is never forgiven: only an `AdapterError` is, because the
      state a run yielded last can predate a verdict the router reached *(review, three times)*
- [x] the trace says the second look never came back, rather than showing a step the run
      took and an answer from before it *(review)*
- [x] the gate does not fire without budget for one search and the answer that reads it, at
      `CORA_MAX_TOOL_ROUNDS` 1 and 2 *(review)*
- [x] a second look whose *search* breaks gives back the answer in hand — the gate asked for
      that search, and it is often the process's first *(review, four times)*
- [x] the gate holds the answer it is second-guessing, so nothing counts rounds to tell a
      failed second look from a failure after one *(review, four times)*
- [x] the reminder the shipped plugin wrote is the one the model is sent back with *(review)*
- [x] **(int)** the plugin cora actually ships is the one under test, for both its grounding
      and its prompt — every other test here builds its own *(review)*
- [x] **(int)** all three through the assembled app, not a stub runner *(review)*
- [x] once nudged, a final reply routes to `done` even with no search — the gate fires once
      per run, so a run can never loop on it
- [x] the tools used are read from the transcript's own tool calls, not from the trace

#### `GroundStep`

- [x] it appends the plugin's reminder as a system message and marks the run nudged
- [x] it records the reconsideration in the trace as its own kind of step

#### A plugin says whether it wants this

- [x] `Plugin.grounding` defaults to empty, so a plugin that opts out routes straight to
      `done`
- [x] the fitness plugin asks for grounding, and its prompt tells the model to answer from
      the documents rather than "the retrieved context" — the sprint-3 line that assumed
      context was already there

#### The whole run

- [x] **(int)** a first answer that skipped the documents is sent back, and the second
      answer arrives after a search
- [x] **(int)** the trace shows the reconsideration between the two answers
- [x] **(int)** a greeting is still answered without retrieving
- [x] the round budget still trips before the graph's own limit when the gate has added a
      round — the gate needs no extra allowance, because its nudge takes the superstep the
      interrupted round would have spent on tools (the allowance was removed)

#### The gate weighs evidence instead of asking for compliance

Run against a real model, the nudge sent small talk to the documents: "Hi there!" searched
for `"Hi there!"` and came back citing a protein passage. The gate reads the evidence itself
now, so the model revises against what the documents say rather than being told to go and
look.

- [ ] `GroundStep` searches the question itself and appends the passages it found, so the
      second look weighs evidence rather than an instruction
- [ ] the appended passages carry the untrusted-data label, like any other document text
      that reaches the model
- [ ] the sources it found are registered on the state, numbered after those already known
- [ ] a search that matches nothing says so in the message it appends, rather than implying
      there is evidence to weigh
- [ ] the trace names the search the gate ran and what came back, so a citation in the
      revised answer has a visible origin
- [ ] the reconsideration step no longer says it sent the answer back to search
- [ ] a second look costs one round, not two, so the budget lets it through on less room
- [ ] the shipped plugin asks the model to weigh the passages it was given, not to call
      `search_documents`
- [ ] a gate whose own search fails keeps the answer rather than losing it, and the trace
      says the look failed — the search is the gate's now, so its failure is the gate's too
- [ ] a second look that never came back is still told from one that did: the gate registers
      sources itself, so "no source was found" no longer proves the model never replied
- [ ] **(int)** a greeting whose evidence is irrelevant keeps its answer, cites nothing, and
      shows no sources — it does query the index, which the old wording called "not touching
      the documents"

#### Close

- [ ] **(llm)** a real model, asked a plain training question that never mentions documents,
      answers with a citation — and the same run's greeting cites nothing. **Written, not
      run**: the llm tier needs a real key, so this is the one item that cannot be ticked
      from a green suite. Run it before merge.
