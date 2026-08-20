# Story 24: cora asks when it cannot tell

**As a** user · **I want** to be asked when my own facts contradict each other · **So that**
the answer rests on the one I meant, not on a guess I never saw

> **Given** memory holds the same fact more than once, with different values, and nothing
> in it says which is current
> **When** I ask a question whose answer depends on that fact
> **Then** cora stops and asks which value to use, and answers with the one I pick — and
> declining leaves memory untouched

Nothing here is keyed to a fact: any remembered fact recall returns twice over can raise
the question, and three bodyweights behind a BMR is one case of it. The pause is a tool
the model calls, not a gate on a step the plugin marks, because the card has to ask
*which of these did you mean?* — which needs the values and where each came from.
LangGraph's `interrupt()` parks the run; the pick resumes it.

## Test list

**Tiers:** unit unless marked — **(int)** integration, **(vitest)** page, **(browser)**
real cascade, **(llm)** live model.

#### The outer test

- [ ] a question that depends on a fact memory holds three times over, in conflict, pauses
      with those three values as its options, and resuming with one answers using it —
      `xfail(strict=True)` until the list below is done

#### What a checkpoint may hold (`domain/decision.py`)

- [ ] a `Decision` written through a checkpoint comes back a `Decision`, not a dict — it
      and `Option` are in the serde allowlist

#### The tool the model calls (`engine/ask_tool.py`)

- [ ] the schema accepts a question, its options and a decline line
- [ ] an option is a label alone when the model offers no note
- [ ] a plugin tool named `ask_user` is rejected at assembly rather than silently
      shadowed, as `search_documents` already is

#### Router

- [ ] a reply calling `ask_user` routes to `ask`
- [ ] a reply calling `ask_user` beside another tool still routes to `ask`
- [ ] the ask lands before any tool of its round — nothing has run when the pause happens,
      so the resume replays nothing
- [ ] an ask round does not spend a tool round — a question asked mid-run cannot exhaust
      the budget the answer still needs

#### `AskStep`

- [ ] the step hands its pause a `Decision` carrying the question, the options in the
      model's order, and the decline line
- [ ] the chosen label comes back as the `ask_user` tool message
- [ ] declining comes back as a tool message saying the reader chose nothing
- [ ] a malformed `ask_user` call comes back as a tool error and never pauses
- [ ] a second ask in the same turn is refused as a tool error — a turn pauses once

#### `ToolStep`

- [ ] a round mixing `ask_user` with another call runs only the other call — the ask
      already carries its own message
- [ ] a round that asks and writes to memory pauses before the write, and after resuming
      the write happens exactly once

#### `Agent`

- [ ] a run that pauses returns `Pending` carrying the question and the decision
- [ ] a paused run records no turn
- [ ] a paused run does not raise `GraphRunError`, although the stream yielded once
- [ ] a paused run is not reported as an empty answer
- [ ] `resume` continues the run and returns the answer
- [ ] the resumed turn is recorded, once, with the question that opened it
- [ ] `pending` is `None` for a thread that never paused

#### `LangGraphRunner`

- [ ] over fake steps whose ask node pauses, `run` drains and `pending` reports the
      parked decision
- [ ] `resume` hands the answer back into the ask node and the run finishes
- [ ] a decline arrives at the ask node as nothing chosen
- [ ] resuming a thread with nothing parked raises a `CoreError`, not a library error

#### ⇄ Switchover (one commit: the tool is offered and the pause is wired)

- [ ] `assemble` offers the model `ask_user` beside `search_documents` and `remember`
- [ ] the assembled agent pauses on a scripted `ask_user` call and answers after a resume
- [ ] `ASK_RULE` reaches the brief, ahead of the facts it governs
- [ ] the Streamlit page declines a pause and shows the answer it produced

#### The API

- [ ] a turn that pauses ends its stream with `paused`, after the steps it took
- [ ] the `paused` payload carries the question, the options with their notes, and the
      decline line
- [ ] `POST /api/resume` streams the rest of the turn and ends with `turn`
- [ ] a resume with no answer declines and still answers
- [ ] a resume on a thread with nothing parked is refused as a sentence, not a traceback
- [ ] a resume without a thread is refused like a question without one
- [ ] `GET /api/sessions/{thread}/pending` returns the parked decision
- [ ] it returns nothing for a thread with none

#### The page

- [ ] **(vitest)** a `paused` frame draws the card with its question and its options
- [ ] **(vitest)** an option's note is drawn beside its label
- [ ] **(vitest)** clicking an option resumes the turn, and the answer replaces the card
- [ ] **(vitest)** the resolved line names what was chosen
- [ ] **(vitest)** declining resumes with nothing chosen
- [ ] **(vitest)** `Change` puts the options back
- [ ] **(vitest)** picking again after `Change` asks a new turn rather than resuming
- [ ] **(vitest)** reloading while a card waits redraws it from the pending route
- [ ] **(vitest)** a card arriving scrolls the conversation down to it
- [ ] **(vitest)** the composer says why it is unavailable while a card waits, rather than
      going missing from the page

#### Close

- [ ] **(llm)** a real model, handed a fact recalled at three conflicting values, asks
      which one to use instead of picking — the honest proof that the pause is its decision
