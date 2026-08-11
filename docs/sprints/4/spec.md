# Sprint 4 — cora becomes an agent

The assignment (`assignment.md`) asks for an AI agent that solves a real problem.
This file cuts its five task requirements into stories with acceptance criteria.
Anything that maps to no story here is out of scope.

## Purpose (requirement 1)

cora is a **document-grounded agent**: point it at your own documents, ask in your own
words, and it plans the steps itself — looking things up when it needs to, running the
domain's tools, remembering you between sessions, and asking you when a decision is
yours.

The domain is not in the agent. It comes from a plugin, and a plugin may bring its own
specialist agents. The shipped plugin (fitness coaching) is the worked example, not the
product.

**Target users:** people with a body of their own material and recurring questions over
it. Today they either read it all again or ask a generic chatbot that has never seen it.

## Architecture decision

The agent runs on **LangGraph** — the graph, the checkpointer (thread memory), the store
(long-term memory) and `interrupt()` (human-in-the-loop) are the wheel we don't re-cut,
and they are what this sprint is marked on.

It stays hexagonal: `cora.core` keeps the agent's state shape and its steps as plain
functions; an adapter wires those steps into a `StateGraph`. Core does not import
LangGraph, so the framework-free architecture test stands unchanged. If keeping that
purity starts contorting the port, we weaken the rule deliberately and record why — not
pre-emptively.

`ChatEngine` is refactored into those steps rather than kept beside them: one agent, not
two paths.

**A fifth port.** Driving the graph is a technology the core must not name, so the `Agent`
facade in core reaches its runner through a new port and `assemble` binds
`LangGraphRunner` to it like the other four. The core has said "four ports" so far; this
sprint makes it five, deliberately. The line it follows is the one the code mostly draws:
`core/ports/` holds Protocols whose implementations live *outside* core, while
collaborator Protocols implemented *inside* it (`ContextSource`, `InputValidator`,
`ToolExecutor`) sit beside the service that uses them. A heuristic, not a law —
`ValidationRule` sits in `ports/plugin.py` with three core implementations, and
`Bm25KeywordIndex` satisfies `ContextSource` from outside. The alternative — moving `Agent`
into the shell to avoid the port — would push the assembly of `ChatResult` into the
composition root and leave the core with no use case.

The **router stays in core**: a plain function from state to the next step, budget check
included. The adapter contributes edges and nothing else, so the one decision worth
testing needs no LangGraph. `big-picture.md` is redrawn around this at merge.

## Stories

In merge order. Each ends on main as a working, demoable app. A story in flight moves
into its own file and leaves a pointer behind.

### [1. The agent plans its own steps](done/story-01.md) ✔

### [2. I can see what it did](story-02.md)

### 3. It remembers me between sessions

> **Given** I told it something about myself last session
> **When** I reopen the app and ask a question that depends on it
> **Then** the answer reflects it without me repeating it, and I can see and clear what
> it remembers

Satisfies the medium bonus *long-term / short-term memory*.

### 4. It asks before acting

> **Given** the agent reaches a step the plugin marks as needing approval
> **When** it gets there
> **Then** the run pauses for approve / edit / reject, and approving resumes from the
> pause, not from the start

### 5. A plugin can bring its own agents

> **Given** a plugin declares a specialist
> **When** I ask something in that specialist's area
> **Then** the agent delegates to it and the answer says which one handled it — and a
> second specialist needs no core change

### 6. Guard rails, developer settings out of the way *(bonus)*

> **Given** I am a normal user
> **When** I open the app
> **Then** no model picker, prompt box or retrieval knob is visible — with `CORA_DEV=1` a
> developer panel exposes them, and an injection attempt is refused before the model is
> called

Satisfies the medium bonus *security guard + developer settings separated from the user
experience*.

### 7. More tools, user-toggled *(bonus, stretch)*

> **Given** five tools, one of them calling an external API
> **When** I disable one in the UI
> **Then** the agent can no longer use it

Cushion only — cut first if the hours run out.

## Requirement coverage

| Requirement | Where |
|---|---|
| 1 · Agent purpose | *Purpose* above; restated in `README.md` |
| 2 · Core functionality | Stories 1, 3, 4, 5 |
| 3 · User interface | Stories 2, 4, 6 |
| 4 · Technical implementation | *Architecture decision* above, plus the failure criteria carried by every story (below) |
| 5 · Documentation | Ships with each merge: `README.md` usage, three worked examples, decisions recorded here, `big-picture.md` redrawn around the agent |

**Error handling is not its own story.** Every story carries its failure criterion:
provider failure, tool crash and step-budget exhaustion each end as one friendly message
with the conversation intact and a retry available.

## Bonus bar

Two medium plus one hard is the maximum-points bar. Cleared by core work — agentic RAG
(story 1, hard) and memory (story 3, medium) — plus story 6 (medium). Story 7 is the only
cushion.

## Out of scope

- A second domain plugin. The plugin seam is proven by story 5, not by a new domain.
- Multi-model support, authentication, token/cost display, observability, eval reports —
  not chosen for the bonus bar this sprint.
