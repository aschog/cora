# Sprint 4 — cora becomes an agent

The assignment (`assignment.md`) asks for an AI agent that solves a real problem. This file
cuts its five task requirements into stories with acceptance criteria, and records which of
them shipped. Anything that maps to no story here is out of scope.

## Purpose (requirement 1)

cora is a **document-grounded agent**: point it at your own documents, ask in your own
words, and it plans the steps itself — looking things up when it needs to, running the
domain's tools and remembering you between sessions.

The domain is not in the agent. It comes from a plugin. The shipped plugin (fitness
coaching) is the worked example, not the product.

**Target users:** people with a body of their own material and recurring questions over
it. Today they either read it all again or ask a generic chatbot that has never seen it.

## Architecture decision (requirement 4)

The agent runs on **LangGraph** — the graph, the checkpointer (thread memory) and the store
(long-term memory) are the wheel we don't re-cut, and they are what this sprint is marked
on.

It stays hexagonal: `cora.domain` keeps the agent's state shape and `cora.engine` its steps
as plain functions; an adapter wires those steps into a `StateGraph`. Neither imports
LangGraph, so the framework-free architecture test stands unchanged.

`ChatEngine` was refactored into those steps rather than kept beside them: one agent, not
two paths.

**Two new ports.** Driving the graph is a technology the core must not name, so the `Agent`
facade reaches its runner through `GraphRunner` and `assemble` binds `LangGraphRunner` to
it. Story 3 adds `Memory` on the same line: four verbs of intent rather than a key-value
store, and the one slot that may be left empty — an app assembled without it is offered no
`remember` tool at all. Both follow the line the code mostly draws: `ports/` holds
Protocols whose implementations live *outside* the engine, while collaborator Protocols
implemented *inside* it (`ContextSource`, `InputValidator`, `ToolExecutor`) sit beside the
service that uses them.

The **router stays in core**: a plain function from state to the next step, budget check
included. The adapter contributes edges and nothing else, so the one decision worth testing
needs no LangGraph. `big-picture.md` is drawn around this.

## Stories shipped

In merge order. Each ended on main as a working, demoable app; each story's text and test
list live in its own file under `done/`.

### [1. The agent plans its own steps](done/story-01.md) ✔

### [2. I can see what it did](done/story-02.md) ✔

### [3. It remembers me between sessions](done/story-03.md) ✔

Three more stories surfaced during the sprint and were numbered from 8 so the planned
numbers above kept their references:

### [8. It answers from my documents](done/story-08.md) ✔

The backlog's *no grounding or scope decision*, found in use.

### [9. The layout says what the architecture is](done/story-09.md) ✔

### [10. One core, many frontends, many plugins](done/story-10.md) ✔

Structural refactors: no user-facing change, no bonus.

## In flight

### [11. The plugins I choose, or none](story-11.md)

cora becomes domain-agnostic by default: `CORA_PLUGINS` takes an ordered list, a plugin
contributes whatever it has, and the prompt-injection guard becomes the one plugin the
default set ships. The backlog's *stronger injection rules as a plugin* is blocked on it.

### [12. It says when it has nothing to answer from](story-12.md)

An in-scope question against an empty store is answered from model knowledge today. After
story 11 cora words the grounding reminder, and it says it has no documents instead.

## Not built this sprint

Planned, cut once the bonus bar was cleared and the hours ran down. None of them is needed
for a task requirement:

- **Human-in-the-loop approval** (pause on a step the plugin marks as needing approval,
  approve / edit / reject, resume from the pause). LangGraph's `interrupt()` is the whole
  mechanism; the cost is the UI and the resume path. The most interesting of the five and
  the first thing to pick up next sprint.
- **Plugin-supplied specialist agents** (delegate to a declared specialist, second one
  costs no core change). The plugin seam is already proven by the shipped plugin's tools,
  prompt, validation rules and seed documents.
- **A developer panel behind `CORA_DEV=1`.** There is nothing to hide: every model, prompt
  and retrieval knob is already environment-only, so the separation the bonus asks for
  holds by construction (see *Bonus bar*).
- **Tool toggles in the UI.** Five tools ship, but they are bound at assembly time, so a
  toggle means rebuilding the app or threading enabled-ness through the graph — a slice,
  not a checkbox.
- **Entry-point plugin discovery** (`[project.entry-points."cora.plugins"]` instead of the
  `CORA_PLUGIN` module path). Story 10 made a plugin a distribution, which is the half that
  mattered; naming it in a manifest is a later convenience.

## Requirement coverage

| Requirement | Where |
|---|---|
| 1 · Agent purpose | *Purpose* above; restated in `README.md` |
| 2 · Core functionality | Stories 1, 3, 8 — plan, tools, retrieval as a decision, memory |
| 3 · User interface | Story 2 (trace), story 3 (memory panel), plus upload, sources and chat in `README.md` § *Run the app* |
| 4 · Technical implementation | *Architecture decision* above, plus the failure criteria carried by every story (below) |
| 5 · Documentation | `README.md` setup and usage, worked examples of asking, remembering and small talk, decisions recorded here, `big-picture.md` drawn around the agent |

**Error handling is not its own story.** Every story carries its failure criterion:
provider failure, tool crash and step-budget exhaustion each end as one friendly message
with the conversation intact and a retry available.

## Bonus bar

Two medium plus one hard is the maximum-points bar. Cleared:

- **Hard 1 · Agentic RAG** — story 1. Retrieval is a tool the model decides to call, not a
  fixed step before the answer; story 8 adds the grounding gate behind it.
- **Medium 2 · Long-term and short-term memory** — story 3. LangGraph's checkpointer owns
  the thread, its store owns the facts, and a `remember` tool plus a sidebar panel put both
  in the user's hands.
- **Medium 8 · Security guard, developer settings out of the user experience** — the
  validation pipeline refuses prompt injection before the model is called
  (`engine/validation.py`) and the plugin adds its own medical rule; retrieved document text
  reaches the model as an untrusted-data `tool` message, never as system authority (story
  1). The user's screen carries documents, memory, chat and the trace — no model picker,
  prompt box or retrieval knob; those are environment variables only (`app/config.py`).

## Out of scope

- A second domain plugin. The plugin seam is proven by the shipped one, not by a new domain.
- Multi-model support, authentication, token/cost display, observability, eval reports —
  not chosen for the bonus bar this sprint.
