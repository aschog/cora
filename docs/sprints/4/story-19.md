# Story 19: The answer arrives as it is written

**As a** reader · **I want** the answer to appear as cora writes it · **So that** a turn
that takes a minute reads as an answer being written rather than a page that has stopped

> **Given** a document indexed and a question asked in the React page
> **When** cora writes the answer
> **Then** it appears piece by piece as it is written, and once the turn lands its
> citations are clickable

The steps of a turn already arrive live; the answer does not. `/api/ask` is a stream
carrying `step` events and then one `turn` event with the finished text, so the page shows
`Working…` for as long as the model takes and then the whole answer at once.

**Why the stream is not enough on its own.** `Agent.answer` reports steps by *diffing*
`state["trace"]` between the states `GraphRunner.run` yields, and a graph yields only
between steps. The answer is written *inside* the model step, so nothing written there has
a way out. A sink has to travel in.

**The sink is bound per run.** `ports/graph.py` names `TextSink` beside `DONE` and `TOOLS`
— a graph engine is told the vocabulary of a turn, and this is now part of it — and
`GraphRunner.run` takes one. `GraphFor`'s `model` slot widens from a `Step` to a
`Callable[[TextSink], Step]`: `ModelStep` gains an `on_text` field and hands assembly a
bound `writing_to`, and `LangGraphRunner` calls it when it adds the node. The graph is
already rebuilt on every `run`, so this costs the runner nothing — and it is what makes
the sink *this turn's*, which two tabs asking at once need, because each turn runs on its
own thread.

**A `str`, not a labelled event.** One kind of thing goes out this way today. Deltas are
ephemeral — never checkpointed, never replayed — so widening `str` to a union later is a
typed refactor `ty` enumerates, with no stored shape to migrate. That is what tells this
apart from `TraceStep`, which is a labelled union *because* it is written to the
checkpoint.

**A preamble is superseded, not blanked.** A model that writes before calling a tool has
that text recorded already, as `ModelDecision.detail` in the trace. So the page keeps a
live buffer and resets it on the *first delta after a step arrived* — never on the step
itself, which would blank the finished answer for the frame between its step and its
`turn` event. Both callbacks reach the browser through the one `asyncio.Queue` in `_ask`,
so they are ordered against each other.

Citations stay literal `[1]` while streaming: `answerHtml` needs the resolved citation
set, which exists only once the answer is whole. The `turn` event redraws it clickable.

## Test list

**Tiers:** unit unless marked — **(int)** integration, **(ui)** vitest via `make ui-test`.

#### The model step writes as it goes (`engine/steps.py`)

- [ ] a model step given a sink hands it the pieces the model wrote, in order
- [ ] the state it returns is unchanged by the sink — `answer` is still the whole reply
- [ ] a step given no sink answers as it always did
- [ ] `writing_to` returns a step bound to that sink and leaves the original writing
      nowhere, so one assembled app serves two turns without them crossing

#### The graph carries it in (`adapters/langgraph_runner.py`)

- [ ] `run` gives its sink to the model node, so text written inside the node reaches the
      caller
- [ ] two runs with two sinks do not cross — each turn's text reaches only the sink it was
      asked with
- [ ] a run asked with no sink takes the same turn

#### One turn, reported as it happens (`engine/agent.py`)

- [ ] `answer` hands text to `on_text` as it arrives and still returns the whole answer in
      its `ChatResult`
- [ ] a caller that passes no `on_text` gets the same result — Streamlit is untouched
- [ ] the text reported is this turn's: a resumed thread replays no earlier turn's writing
- [ ] a turn that fails keeps the text already reported, as it already keeps its steps

#### The adapter streams (`adapters/openrouter_chat_model.py`)

- [ ] the client is asked to stream, and each piece of content reaches the sink
- [ ] the aggregated reply is the `ModelReply` a whole response would have given — same
      text, same tool calls
- [ ] a stream that ends on `finish_reason: length` with no tool call still raises
      `LlmTruncatedError`
- [ ] a stream whose text aggregates to blank and calls no tool still raises
      `LlmEmptyReplyError`
- [ ] reasoning reaches no sink — what the model thinks is not what it answered
- [ ] a tool call reaches no sink either
- [ ] a stream that fails part-way surfaces as the categorised `LlmError`, the pieces
      already sent left standing

#### The wire says it twice, once as it arrives (`frontends/react/api.py`)

- [ ] `/api/ask` sends a `text` event per piece the turn writes
- [ ] a piece arrives before the `step` event that ends the round it was written in
- [ ] the `turn` event still carries the whole answer, so the page never assembles it
- [ ] a turn that fails after writing ends with `error` and nothing further

#### The page grows the answer (`ui/api.ts`, `App.tsx`, `Answer.tsx`) **(ui)**

- [ ] **(ui)** `ask` reports each `text` frame to its caller and still resolves with the
      `turn` result
- [ ] **(ui)** a pending turn shows what has been written instead of `Working…`
- [ ] **(ui)** a pending turn with nothing written yet still says `Working…`
- [ ] **(ui)** the first piece after a step arrived starts a new answer — a preamble
      before a tool call is replaced, not appended to
- [ ] **(ui)** a step arriving does not on its own clear what has been written
- [ ] **(ui)** text written in a conversation the reader has left does not land on the
      page, as its answer already does not
- [ ] **(ui)** the turn landing redraws the answer with its citations clickable
- [ ] **(ui)** a turn that fails after writing shows the error in place of what was written
- [ ] **(ui)** the conversation follows the answer down as it grows

#### Outer functional test

- [ ] **(ui)** `xfail`/`skip` until the list is done: a question asked against a stubbed
      streaming response shows the answer growing, and when the turn lands its `[1]` is a
      button that opens the passage
- [ ] **(int)** the same over the HTTP surface: the pieces a scripted turn streams,
      concatenated, are the answer its `turn` event carried

The `llm` tier spends money and is the human's to run: Phase 4 checks a real model's
answer arriving in pieces.

`Written` re-parses markdown whenever the answer changes, which is now once per piece
rather than once per turn. Named here because it is the one thing this story makes
measurably more expensive; nothing is built for it until a turn is slow because of it.
