# Story 2: I can see what it did

**As a** user · **I want** to see the steps behind an answer · **So that** I can tell what
it looked up, what it ran, and whether to believe it

> **Given** an answer that took several steps
> **When** I expand the trace
> **Then** each step shows the decision, the tool and its arguments, and what came back

Closes manual finding #5 — raw, unlabelled payloads printed beside the answer.

## Test list

**Tiers:** unit unless marked — **(int)** integration, **(e2e)** browser, **(llm)** live
model. **(migrated)** marks a test that moves rather than a new one.

#### The outer test (`tests/test_trace.py`)

- [x] **(int)** a turn that searches and calculates shows a trace naming both tools, their
      arguments and what each returned — and no payload outside it

#### `TraceStep` (`core/trace.py`)

- [x] a decision that asked for tools summarises as "Decided to call search_documents",
      two tools joined
- [x] a decision that asked for none summarises as "Decided no tool was needed" — it reads
      the same as the last step of a long run and as the only step of a greeting
- [x] a decision's detail is the prose the model sent alongside its tool calls
- [x] a tool use summarises as the tool's name, its arguments as `name=value` in the order
      given, and the outcome
- [x] a call with no arguments summarises as the bare name
- [x] a failed tool use is marked failed and its outcome is the tool's error

#### A citable payload describes itself (`citations.py`)

- [x] `Citable` requires a `summary` beside `register`, so a plugin's own citable payload
      phrases its own outcome
- [x] `CitableHits.summary` counts the passages and names the distinct sources in order
- [x] a single hit reads "1 passage", not "1 passages"
- [x] no hits reads "no matching documents"

#### The steps record what they did

- [x] `ModelStep` appends one decision naming the tools the reply asked for
- [x] a final reply's text is the answer, so its decision repeats none of it as detail
- [x] `ToolStep` appends one step per call, in order, each carrying the tool's name and the
      arguments it was called with
- [x] a citable payload's outcome is the payload's own summary and its detail is the
      numbered block that was registered — the untrusted-data label stays out of it
- [x] a plain payload's outcome and detail come from the result's `render()`
- [x] a failed call appends a step marked failed, and no `ToolResult` reaches the user
- [x] `AgentState.trace` accumulates across steps; `tool_results` is deleted from the state
      and from `ChatResult`, its callers re-pointed at the trace *(migrated)*

#### The run streams (`GraphRunner` port, `LangGraphRunner`)

- [x] `run` yields the accumulated state after each step, the last one carrying the run
      *(migrated)*
- [x] the caller sees a step before the run ends — pulling one state leaves the later steps
      uncalled
- [x] a runaway graph still surfaces as `ToolLoopLimitError` while iterating, never
      `GraphRecursionError` *(migrated)*
- [x] an `InputRejectedError` from `PrepareStep` travels out of the iteration unwrapped
      *(migrated)*
- [x] an `AdapterError` raised inside a step does too *(migrated)*

#### `Agent`

- [x] `answer` still returns the answer and its cited sources over a streaming runner
      *(migrated)*
- [x] `ChatResult.trace` carries the run's steps in order
- [x] `on_step` is called once per step as it arrives, before the run finishes
- [x] a step already reported is never reported again
- [x] when the run fails midway the error propagates, and the steps already reported stand

#### Rendering (`app/ui/formatting.py`)

- [x] a step renders as its summary line; a failed step is marked as failed
- [x] its detail follows as a fenced block, and a detail past the cap ends in a truncation
      marker
- [x] a step with no detail renders the summary alone

#### The trace on screen (`app/ui/chat.py`)

- [x] **(int)** the finished turn carries a collapsed "How I got there" naming the tool,
      its arguments and what came back
- [x] **(int)** the answer bubble prints no raw payload — the "Tool results" expander is
      gone *(finding #5)*
- [x] **(int)** the trace survives a rerun: after a second question the first answer still
      carries its own steps
- [x] **(int)** a turn whose tool failed shows the failed step and still shows the answer
- [x] **(int)** a run that ends in an error shows the error with the steps taken so far
      beside it — they can only have come from `on_step`, which is what proves the UI
      draws them while the run is still going
- [x] **(int)** a greeting shows the one-step trace that says no tool was needed

#### Found by the review

- [x] a document carrying its own code fence cannot forge trace lines — the evidence is
      rendered as code, never as markdown
- [x] nor can it forge one through the summary, which names the tool the model asked for:
      a step line is one line, and only the marks cora wrote are markdown *(review, twice)*
- [x] a tool's escaped exception reaches neither the model nor the trace by its message,
      only by its kind — a refusal is declared (`ToolRefusal`), not guessed from a type, so
      a library's accidental `ValueError` is treated as the escape it is *(review, twice)*
- [x] the caller really does see a step before the run is over — the old test only showed
      that the seed state arrives before any node runs
- [x] a payload that only looks citable is asserted against a literal, not against a value
      recomputed the way the code computes it
- [x] a runner that walks no step at all is a `GraphRunError`, not a blank answer

#### Close

- [x] **(e2e)** the browser trace opens and names the search tool, its query and its
      outcome — re-points `test_chat.py` and the tool evidence in `test_llm_acceptance.py`,
      whose greeting assertion moves from "no expanders" to "no Sources"
- [x] `README.md` and `big-picture.md` say the run is traced
