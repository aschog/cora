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

- [x] a final reply with no search behind it routes to `ground` when the plugin asks for it
- [x] a final reply that followed a search routes to `done`
- [x] once nudged, a final reply routes to `done` even with no search — the gate fires once
      per run, so a run can never loop on it
- [x] the search is looked for in the transcript's own tool calls, not in the trace

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
- [x] the recursion limit leaves room for the extra round the gate can add

#### Close

- [ ] **(llm)** a real model, asked a plain training question that never mentions documents,
      answers with a citation — replaces the live test that gave the answer away by asking
      "according to my documents". Written; needs a run with `OPENROUTER_API_KEY`
