# Story 20: Nothing reaches the reader as an answer but the answer

**As a** reader · **I want** everything the page offers me as cora's answer to be an answer
cora actually gave · **So that** an answer with no citations means no documents were
needed, not that a search went missing

> **Given** a model that malforms the arguments of the search it asked for
> **When** I ask a question about my documents
> **Then** the turn ends as one friendly sentence, and none of the model's prose is offered
> as the answer

> **Given** a model that writes "Let me check your notes." before it calls a tool
> **When** the answer arrives
> **Then** the page says `Working…` for that round rather than showing the aside, and a
> client reading the stream can tell an aside from the answer without inferring it

> **Given** an answer being written
> **When** I scroll up to re-read an earlier turn
> **Then** the page leaves me where I am until I come back to the bottom

Closes the *Before submission* block of `manual-test-findings.md` — #26, #16, #18, #23 —
and #17 and #20 with them, which are #16's root at two other layers.

The three code findings are one mistake at three layers: something that is not the answer
is presented as the answer. A tool call whose arguments did not parse is dropped, so
`reply.tool_calls` is empty, the reply reads as final and the model's prose is served
ungrounded (#26). A round's writing reaches the reader whether or not that round turned out
to be the answer, so the contract `README.md` and `_ask` state — the pieces concatenate to
the answer — is false, and every client has to infer round boundaries from `step` events
(#16, #17, #20). And the scroll effect now runs per piece, so it pins the reader to the
bottom for the whole of a streamed answer (#18).

## Test list

**Tiers:** unit unless marked — **(int)** integration, **(ui)** vitest via `make ui-test`.

#### The tool call that did not parse (`adapters/openrouter_chat_model.py`, `domain/errors.py`)

- [x] a reply whose tool-call arguments did not parse raises rather than answering — prose
      is not an answer when the search it asked for never ran
- [x] a reply carrying one call that parsed and one that did not raises too: a dropped
      intent is a dropped intent
- [x] the parse error each invalid call carries reaches the log, and the sentence the
      reader gets carries none of it
- [x] a streamed tool call whose argument JSON never completes aggregates into an invalid
      call and raises
- [x] a reply with no tool calls of either kind still answers, truncates and empties
      exactly as it did

#### The sink is told which round wrote to it (`ports/chat_model.py`, `engine/steps.py`)

- [x] the pieces reach the sink as `Piece`, in the order they were written
- [x] a round that ends in a tool call tells the sink its writing was an aside, after the
      pieces of it
- [x] a round that ends in an answer tells it nothing further
- [x] the state the step returns is unchanged either way — `answer` is still the whole
      final reply
- [x] a step given no sink answers as it always did

#### The wire marks the boundary (`frontends/react/api.py`)

- [x] `/api/ask` sends an `aside` event after the pieces of a round that called a tool
- [x] the `aside` arrives before the `step` event that ends the round it belongs to
- [x] a turn answered in one round sends no `aside` at all
- [x] the `text` pieces after the last `aside` are exactly the answer the `turn` event
      carries, for a model that writes before it searches

#### The page believes the wire instead of guessing (`ui/api.ts`, `App.tsx`) **(ui)**

- [x] `ask` reports the `aside` frame to its caller and still resolves with the `turn`
- [x] an aside puts the turn back to `Working…`, rather than leaving a superseded preamble
      where the answer goes for the whole tool round
- [x] the answer written after an aside starts clean — the aside is not prepended to it
- [x] a `step` event clears nothing on its own, because the page no longer infers a round
      boundary from one

#### The reader keeps their place (`ui/components/Answer.tsx`) **(ui)**

- [x] a reader who has scrolled up is not pulled down as the answer grows
- [x] a reader at the bottom is still followed down, as story 19 asked
- [x] a reader who scrolls back to the bottom is followed again
- [x] asking a question scrolls to it from wherever the reader had scrolled to

#### Outer functional tests

- [x] **(int)** over a scripted model that writes a preamble, calls a tool and then
      answers, the pieces after the last `aside` concatenate to the answer the `turn` event
      carried — `test_react_frontend.py`'s assertion held by construction rather than by a
      script whose preamble happens to be empty
- [x] **(int)** a turn whose tool call is malformed ends as an `error` event with one
      friendly sentence and no `turn`, with nothing of the model's prose on the wire

#### The docs say what is true

- [x] ~~`README.md` and `_ask`'s docstring state the contract the stream now keeps~~ — no
      test to write: `tests/guards/test_docs.py` checks that the paths a page names
      resolve, not that its prose is true. The tests above are what make the sentence
      true; this is writing it down
- [x] ~~`spec.md`'s coverage table cites stories 16–19 and the React frontend~~ — no test,
      and deliberately: the guard leaves `docs/sprints/**` alone, because a record that
      follows the code is not a record

#### Found while building it

- [x] an aside for a round that wrote nothing is noise on the wire — it exists to have a
      reader drop what they were shown, so it fires only when that round wrote
- [x] three standing scroll tests set `scrollTop` to 0 to observe the write, which under
      the guard reads as *the reader scrolled up*. They say "the reader is at the bottom"
      now, in one helper; the assertion they make is unchanged

Whether a malformed tool call should be retried was the open decision in #26. It ends the
turn: `to_model_reply` already raises rather than returns when the provider stopped early,
and a retry would want its own budget beside `max_tool_rounds`.

The `llm` tier is the human's to run: a real model writing an aside before it searches is
what Phase 4 checks, and no scripted model can show it.
