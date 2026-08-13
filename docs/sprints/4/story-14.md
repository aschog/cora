# Story 14: One turn draws itself

**As a** newcomer to cora · **I want** one answered question drawn as a sequence · **So that**
I can see at a glance how a turn works — the model deciding, a tool running, the answer coming
back cited

> **Given** a scripted turn over an indexed document
> **When** I open `docs/diagrams.md`
> **Then** I see the question, each model decision, each tool call with what came back, and the
> answer — and a turn that runs differently fails the suite

## The shape

The turn already reports itself: `ChatResult.trace` carries a `ModelDecision` per model reply
and a `ToolUse` per call, each with the summary the UI shows. So the diagram is a projection of
the trace, not a description of the code — a `ModelDecision` is a call to `ChatModel` and its
answer, a `ToolUse` is a call to the tool and what it returned, and the question and the answer
are the first and last lines.

`render(question, answer, trace)` is therefore pure: the unit tests hand it trace steps
directly, and only the outer test drives a real turn. Driving one needs the fakes in `tests/`,
so the script imports them and the Makefile puts `tests` on `PYTHONPATH` — the scripted turn is
defined once, in the tool, and the test renders the same one.

Rejected: a class diagram of `cora-api`. 49 classes is a 7132pt strip, and the ports on their
own draw ten boxes with no line between them — a picture that says no more than the port table
in `big-picture.md` already does.

## Test list

**Tiers:** unit unless marked — **(int)** integration.

#### First, the outer test

- [x] **(int)** the block regenerated from a real turn is identical to the one committed in
      `docs/diagrams.md` — `xfail(strict=True)` until the generator and the page exist

#### The trace becomes the sequence

- [x] the question is the first line, from the user to the agent
- [x] a `ModelDecision` becomes a call to `ChatModel` and a reply carrying that step's summary
- [x] a `ToolUse` becomes a call to the tool named, with its arguments, and the outcome back
- [x] the answer is the last line, from the agent to the user
- [x] two model rounds render as two pairs, in trace order

#### Mermaid that renders

- [x] the block opens with `sequenceDiagram` and its arrows parse on Mermaid 10.2.3
- [x] a summary carrying `"` or `:` does not break the diagram

#### The page and the command

- [x] `make diagram` writes this page too
- [x] `docs/big-picture.md` links it from **Two calls in**

## Out of scope

- **Prose on the page.** The page is the diagram.
- **Every path through a turn.** One question that searches. A greeting, the grounding gate's
  send-back and a failed tool are each a different turn, and a second diagram if wanted.
- **The class diagram.** Rejected above, not deferred.

## Dropped after the fact

Every test of the generator was deleted at the author's request. `make diagram` regenerates
the block; nothing checks that the committed one is current. The test list above records what was built and passing when the story closed.
