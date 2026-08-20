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
implemented *inside* it (`ContextSource`, `ToolExecutor`) sit beside the
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

The backlog's *no grounding or scope decision*, found in use — and removed again by
story 15, which reopened it.

### [9. The layout says what the architecture is](done/story-09.md) ✔

### [10. One core, many frontends, many plugins](done/story-10.md) ✔

Structural refactors: no user-facing change, no bonus.

### [11. The plugins I choose, or none](done/story-11.md) ✔

cora becomes domain-agnostic by default: `CORA_PLUGINS` takes an ordered list, a plugin
contributes whatever it has, and the prompt-injection guard becomes a plugin named there
like any other. The backlog's *stronger injection rules as a plugin* is blocked on it.

### [13. One package, and only what I asked it to run](done/story-13.md) ✔

The five layer distributions become one `cora` package, the layer guards read imports
instead of manifests to stay true without them, and hybrid retrieval goes so that one
index answers what ingestion wrote. Story 11's default set goes with it: cora starts with
no plugin and warns that nothing screens what the user types.

### [14. One way to search](done/story-14.md) ✔

`advanced` mode rewrote the question behind the search tool, which is the job the agent now
does in the open, one trace step per search. It goes, and the knowledge base is what the
tool searches. Closes the backlog's *planner JSON is hand-parsed* as removed.

### [12. It says when it has nothing to answer from](done/story-12.md) ✔

An in-scope question against an empty store was answered from model knowledge. Cora words
the grounding reminder, so it now tells the two silences apart: nothing uploaded asks for
documents, documents that don't cover the question say so, and small talk is unaffected.

Two more stories were planned after the sprint's review:

### [15. The turn is one path](done/story-15.md) ✔

The grounding gate of story 8 goes, and story 12's two silences with it: a turn runs model
→ tools → done, no plugin names a domain, and nothing holds an answer back. It reopens the
backlog's *no grounding or scope decision* on purpose — the instruction to search and cite
stays, its enforcement was the one branch of the graph that could not be read and defended.

### [16. Read the passage the answer cites](done/story-16.md) ✔

### [17. The React shell is a frontend, not a mockup](done/story-17.md) ✔

### [18. A conversation you can leave](done/story-18.md) ✔

### [19. The answer arrives as it is written](done/story-19.md) ✔

The page showed `Working…` for as long as the model took. The answer is written *inside*
the model step and a graph yields only between steps, so a sink travels in: `ChatModel`
streams, the graph binds the model node to that turn's reader, and `/api/ask` carries a
`text` event per piece. React only — Streamlit waits for the finished turn as it always
did.

### [20. Nothing reaches the reader as an answer but the answer](done/story-20.md) ✔

A tool call the model malforms is dropped before cora sees it, so the round reads as
a final and its prose goes out ungrounded. A round that wrote before calling a tool sent
that aside as `text`, so the contract `README.md` states was false and the page inferred
the boundary from the steps. And a streamed answer pinned the reader to the bottom. The
stream now marks the round it wrote in, and a malformed call ends the turn.

### [21. The page keeps what the reader has, and a failure is called what it is](done/story-21.md) ✔

The *Real bugs, next* block of the manual sweep. A streamed answer re-parsed its markdown
and replaced the whole block on every token, so a reader could not hold a selection long
enough to copy it — the rendered HTML is patched into the block now, node by node. A
duplicate upload was answered with silence, indistinguishable from success; the count the
route already returns is now a notice, and a first upload gets its confirmation too. And
two names were wrong: a failure in the *sink* was reported as the model being unavailable,
and a test claimed a property its two sequential runs could not observe.

### [22. The page stops explaining itself, and a quotation looks like one](done/story-22.md) ✔

The chrome block of the manual sweep. Ten paragraphs explaining the page's own panels are
gone — four standing explanations of a panel already full, six empty states saying what a
panel *will* hold when the tab that opened it already said. The source pane lost the caption
counting marks the reader can see and gained the filename as a heading, which is what the
tests that had used that caption were actually after. `PLAN` became `STEPS`, because the
panel is filled after the answer lands. And the quoted passage is amber: the page's blue
means "click this", so a quotation drawn in it read as a control.

### [23. What an upload did is said beside the list it changed](done/story-23.md) ✔

The notice story 21 shipped moves out of the page-wide banner strip into the documents rail,
under the control that raises it, and gains a dismiss. A duplicate now wears the colour and
the mark the page keeps for an outcome the reader did not ask for — which reverses story 21's
own decision, deliberately and on the record. A document added keeps the accent, so success
does not arrive in an error's clothes.

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
| 2 · Core functionality | Stories 1, 3 — plan, tools, retrieval as a decision, memory |
| 3 · User interface | **Streamlit** — story 2 (trace), story 3 (memory panel), plus upload, sources and chat in `README.md` § *Run the app*. **React** — story 16 (the cited passage, opened), story 17 (the shell over cora's own API), story 18 (leaving a conversation), story 19 (the answer as it is written), story 20 (nothing shown as an answer but the answer), story 21 (the reader's selection kept, an upload's outcome said), story 22 (the page spends its space on the reader's own work, and a quotation reads as one), story 23 (what an upload did, said beside the list it changed), with `make run-react` and the shell's own settings in `README.md` § *Run the app* |
| 4 · Technical implementation | *Architecture decision* above, plus the failure criteria carried by every story (below) |
| 5 · Documentation | `README.md` setup and usage, worked examples of asking, remembering and small talk, decisions recorded here, `big-picture.md` drawn around the agent |

**Error handling is not its own story.** Every story carries its failure criterion:
provider failure, tool crash and step-budget exhaustion each end as one friendly message
with the conversation intact and a retry available.

## Bonus bar

Two medium plus one hard is the maximum-points bar. Cleared:

- **Hard 1 · Agentic RAG** — story 1. Retrieval is a tool the model decides to call, not a
  fixed step before the answer. Story 8 put a grounding gate behind that decision and
  story 15 took it out again: the decision is the model's, asked for in the brief.
- **Medium 2 · Long-term and short-term memory** — story 3. LangGraph's checkpointer owns
  the thread, its store owns the facts, and a `remember` tool plus a sidebar panel put both
  in the user's hands.
- **Medium 8 · Security guard, developer settings out of the user experience** — the
  ordered rules refuse prompt injection before the model is called — the screen is a
  plugin now, `cora.plugins.security`, named in `CORA_PLUGINS` like any other — and the
  fitness plugin adds its own medical rule; retrieved document text
  reaches the model as an untrusted-data `tool` message, never as system authority (story
  1). The user's screen carries documents, memory, chat and the trace — no model picker,
  prompt box or retrieval knob; those are environment variables only (`app/config.py`).

## Out of scope

- A second domain plugin. The plugin seam is proven by the shipped one, not by a new domain.
- Multi-model support, authentication, token/cost display, observability, eval reports —
  not chosen for the bonus bar this sprint.
