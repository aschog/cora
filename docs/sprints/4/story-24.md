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

- [x] a question that depends on a fact memory holds three times over, in conflict, pauses
      with those three values as its options, and resuming with one answers using it

#### What a checkpoint may hold (`domain/decision.py`)

- [x] a `Decision` written through a checkpoint comes back a `Decision`, not a dict — it
      and `Option` are in the serde allowlist

#### The tool the model calls (`engine/ask_tool.py`)

- [x] the schema accepts a question, its options and a decline line
- [x] an option is a label alone when the model offers no note
- [x] a fork with one way out of it is refused — the page offers nothing else while a
      card is open, so a card with one control is a conversation with no way on
- [x] running the tool says the turn has already asked, which is the only way the
      dispatcher reaches it
- [x] a plugin tool named `ask_user` is rejected at assembly rather than silently
      shadowed, as `search_documents` already is

#### Router

- [x] a reply calling `ask_user` routes to `ask`
- [x] a reply calling `ask_user` beside another tool still routes to `ask`
- [x] the ask lands before any tool of its round — nothing has run when the pause happens,
      so the resume replays nothing
- [x] an ask round does not spend a tool round — a question asked mid-run cannot exhaust
      the budget the answer still needs
- [x] a turn that has already stopped the reader routes its next ask to the tools
- [x] an ask that was refused does not spend the turn's question

#### `AskStep`

- [x] the step hands its pause a `Decision` carrying the question, the options in the
      model's order, and the decline line
- [x] the chosen label comes back as the `ask_user` tool message
- [x] declining comes back as a tool message saying the reader chose nothing
- [x] a malformed `ask_user` call comes back as a tool error and never pauses
- [x] a label nobody offered counts as choosing nothing — whatever answered the pause
      came from outside the run

#### `ToolStep`

- [x] a round mixing `ask_user` with another call runs only the other call — the ask
      already carries its own message
- [x] a round that asks and writes to memory pauses before the write, and after resuming
      the write happens exactly once

#### `Agent`

- [x] a run that pauses returns `Pending` carrying the question and the decision
- [x] a paused run records no turn
- [x] a paused run does not raise `GraphRunError`, although the stream yielded once
- [x] a paused run is not reported as an empty answer
- [x] `resume` continues the run and returns the answer
- [x] the resumed turn is recorded, once, with the question that opened it
- [x] `pending` is `None` for a thread that never paused

#### `LangGraphRunner`

- [x] over fake steps whose ask node pauses, `run` drains and `pending` reports the
      parked decision
- [x] `resume` hands the answer back into the ask node and the run finishes
- [x] a decline arrives at the ask node as nothing chosen
- [x] resuming a thread with nothing parked raises a `CoreError`, not a library error
- [x] a turn that keeps asking is stopped by the round budget, not by the graph
      overrunning a limit sized for one pause

#### ⇄ Switchover (one commit: the tool is offered and the pause is wired)

- [x] `assemble` offers the model `ask_user` beside `search_documents` and `remember`
- [x] the assembled agent pauses on a scripted `ask_user` call and answers after a resume
- [x] `ASK_RULE` reaches the brief, ahead of the facts it governs
- [x] the Streamlit page declines a pause and shows the answer it produced
- [x] the notice about a declined question survives a redraw — it belongs to the turn,
      not to the run that drew it

#### The API

- [x] a turn that pauses ends its stream with `paused`, after the steps it took
- [x] the `paused` payload carries the question, the options with their notes, and the
      decline line
- [x] `POST /api/resume` streams the rest of the turn and ends with `turn`
- [x] a resume with no answer declines and still answers
- [x] a resume on a thread with nothing parked is refused as a sentence, not a traceback
- [x] a resume without a thread is refused like a question without one
- [x] a resume that says nothing at all is refused — leaving the answer out reads the
      same as declining, and the thread is still answerable afterwards
- [x] `GET /api/sessions/{thread}/pending` returns the parked decision
- [x] it returns nothing for a thread with none

#### The page

- [x] **(vitest)** a `paused` frame draws the card with its question and its options
- [x] **(vitest)** an option's note is drawn beside its label
- [x] **(vitest)** clicking an option resumes the turn, and the answer replaces the card
- [x] **(vitest)** the resolved line names what was chosen
- [x] **(vitest)** a card that has been answered is not still called paused, and one put
      back up is waiting again
- [x] **(vitest)** declining resumes with nothing chosen
- [x] **(vitest)** `Change` puts the options back
- [x] **(vitest)** picking again after `Change` asks a new turn rather than resuming
- [x] **(vitest)** reloading while a card waits redraws it from the pending route
- [x] **(vitest)** a card arriving scrolls the conversation down to it
- [x] **(vitest)** the composer says why it is unavailable while a card waits, rather than
      going missing from the page
- [x] **(vitest)** a card the model wrote no way out of still has one
- [x] **(vitest)** a resume in the conversation on screen is not called work you left
      behind
- [x] **(vitest)** an answer to a decision does not land on the conversation the reader
      moved to — ids repeat across conversations
- [x] **(vitest)** starting over leaves the parked card behind
- [x] **(vitest)** a card parked in an unrecorded conversation is not lost by reading
      another — a thread that has answered nothing is listed under no session
- [x] **(vitest)** a decision that could not be sent is still answerable, and says what
      went wrong

#### Close

- [ ] **(llm)** a real model, handed a fact recalled at three conflicting values, asks
      which one to use instead of picking — the honest proof that the pause is its decision
