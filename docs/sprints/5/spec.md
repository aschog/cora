# Sprint 5 — the capstone

The assignment (`assignment.md`) is open-ended: seven cases, and any alternative that meets
the criteria. cora is carried forward, not restarted. This file cuts the capstone into
stories with acceptance criteria and records which evaluation criterion each one answers.
Anything that maps to no story here is out of scope.

**Case 2 — an AI agent for task automation.** Case 1's retrieval is what cora does when it
is given nothing else, not the point of it.

The sprint answers one sentence from the review: *cora is not a real agentic application,
it is more like agentic RAG.* That is a fair reading of what shipped. cora decides — whether
to retrieve, how many rounds, which tool, when to stop and ask — but every tool it owns is
another way of reading its own documents, so deciding well only ever produced a better
answer, never an action. This sprint gives it reach and consequence, and a gate in front of
both. The tracked backlog is `sprint-5-feedback.md`; the reviewer's write-up is
`docs/sprints/4/review-feedback.md`.

## Purpose (criterion 1 · outcome quality)

**cora is an agent you chat with, and plugins give it a scope.** With no plugin loaded it
runs a turn on its own: search its documents, remember what it is told, ask when it cannot
tell, and answer grounded and cited. That is where every turn starts, and a scope is what it
becomes.

**A plugin declares its scope, and that scope is the lifetime of everything it contributes**
— instructions, tools, documents and rules alike. This sprint's central decision, and it has
no exceptions:

- **A named scope** is in play only while that scope is active. One scope is active per turn —
  the user pins it, or cora routes to it — and the others are not in the prompt at all. That
  is what focus *means*.
- **`scope=None`** is system-wide: always in the prompt, always callable, always enforced.
  The injection screen lives here, which is why no scope can switch it off.

Three plugins ship: **security** (rules only, always on), **fitness** and **travel** (two
scopes). Two scopes, not one: a second one is the proof that a scope is a plugin and not a
fork — it is written without touching the core — and it is what makes routing worth having,
since one scope leaves nothing to choose between.

**Target users.** People who extend the tools they work in. They want an agent pointed at
their own field by a plugin they wrote and they use what they
extend, which is why the stories below are written from the using side. That makes the plugin
contract the product surface, and `docs/how-to/write-a-plugin.md` part of the product.

## Architecture decision (criterion 2 · learning application)

The agent stays on **LangGraph**, hexagonal: the domain holds the state shape, the engine
holds the steps as plain functions, and only `adapters/langgraph_runner.py` imports the
framework — the architecture guard enforces it. Four decisions are this sprint's.

- **The turn becomes a named sequence, with the loop inside it.** Today `prepare → model ⇄
  tools` is one ReAct loop where a single model call decides everything. It becomes
  *screen → route → work → answer*, each step with one responsibility and its own place in
  the trace; the model keeps the decisions that are genuinely its own, inside the working
  step. Stories 2 and 3.
- **A plugin's scope decides the lifetime of everything it contributes.** One field, one
  rule, no second plugin type: `security` is `scope=None` and therefore system-wide, a domain
  plugin names its scope and everything it brings lives exactly as long as that scope is
  active. Story 3.
- **A scope owns its documents.** The cleaned text a citation opens onto moves from
  `adapters/sqlite_documents.py` to one Markdown file per source, under a directory named
  for its scope, behind the `Documents` port that already exists — which answers the
  reviewer's two store findings together: the duplication goes, and a second domain's layout
  becomes a directory anyone can read. Threads and remembered facts stay in SQLite; they are
  not duplicated raw data. Memory stays system-wide — one person, both scopes. Story 4.
- **An effect is gated by the interrupt that already exists.** Sprint 4 built `interrupt` so
  cora could stop and ask which of two facts was current. A tool that changes something
  outside cora stops the same way: it says what it is about to do and waits. Story 6.

### Shapes the stories must honour

Four constraints, decided here because each one is a *shape* rather than a feature.
`AgentState` and the trace are enumerated in `CHECKPOINTED_DATA`, so they are serialised
into every persisted thread: widening one later is a lock bump and a migration, while
getting it right now costs nothing.

- **Routing yields the active scope*s*, not the active scope.** One scope is the degenerate
  case of a set. A question that spans two scopes is the obvious next ask, and with a set it
  is a later routing rule; with a single value it is a change to the state shape, the prompt
  assembly, the tool filter, the trace and every thread already stored.
- **No plugin loaded *is* a scope.** cora with nothing loaded is agentic RAG over documents,
  and those documents need a directory like any other scope's. A default scope gives one code
  path and one layout rule; "unscoped documents" would give a switch, which is the thing the
  project's north star forbids.
- **The trace has room for a child step, though nothing nests yet.** The sub-agent deferral
  below only holds if the seam survives: a tool that later runs a subgraph must be able to
  *show* its nested work, or cora's "watch what it did" claim goes shallow exactly where the
  interesting work is.
- **An approval is its own checkpointed type, bound to one call.** Sprint 4's `interrupt`
  carries a `Decision` of labelled options for "which fact is current". Squeezing "may I
  write this file" into that shape works for one effect and breaks on the second — two
  effects in one turn, or an argument the user wants to edit before approving, both need the
  approval bound to a specific call.

**One behaviour change this implies:** the fitness plugin's medical filter becomes
fitness-only, so a medical question asked in the travel scope, or with nothing pinned, meets
no filter. The rule is right and its *home* was wrong — a screen that must always apply
belongs in a `scope=None` plugin beside the injection screen, not inside a domain. Story 3
moves it there. Safety is not a domain concern.

**Not decided this sprint:** a sub-agent inside a scope. It needs no new port — `Tool.run`
is a callable and cora never asks what is behind it — but for a plugin to *build* one it
would have to be handed a bounded-loop factory at load time, which widens the plugin
contract. The seam is named in the docs and left unbuilt; a LangGraph subgraph through the
existing `GraphFor` port is where it would go, so the nested steps stay visible in the trace.

---

## Stories

Numbered in merge order. Each becomes an OpenSpec change under `openspec/changes/`, and its
text moves into that change's `proposal.md` when it is opened — this file then keeps the
heading and the link.

### 1. A reader learns what cora is for before anything else

As a person who lands on the repository,\
I want the first screen to tell me what problem this solves and for whom,\
so that I can decide whether it is for me without reading the code.

**Scenario:** the front door explains itself

- **Given** `README.md` as the front door
- **When** someone who has never seen cora reads its first screen
- **Then** they can say what problem it solves, who it is for and how it works
- **And** the showcase entry is linked near the top

Written day one, before the code — the retrospective names cutting it last as the cause of
the reviewer seeing it.

### 2. The turn is a workflow of named steps

As a developer of cora,\
I want a turn to run as a sequence of steps with one responsibility each,\
so that I can see where a turn is, control what each step may do, and test a step without
the whole loop.

**Scenario:** a turn walks its steps

- **Given** any question
- **When** the turn runs
- **Then** the trace names each step it took, in the order the workflow defines
- **And** the rules run before the model is called at all
- **And** a step's failure is reported as that step's, with the conversation intact

**Scenario:** the model's freedom is bounded to one step

- **Given** a question that needs several rounds of tools
- **When** the turn runs
- **Then** the rounds happen inside the working step and nowhere else

### 3. A scope focuses the turn

As a person using cora for one field at a time,\
I want the scope to decide what cora is and what it can reach,\
so that a fitness question is answered by a coach, and a travel tool cannot be picked by
mistake.

The pin is the React shell's only — Streamlit stays unpinned and always routes, which keeps
the routing path exercised by a real frontend rather than by tests alone.

**The travel plugin is not finished by this story.** It arrives here with its instructions and
its corpus, gains its live-service tool in story 5 and its effectful tool in story 6. Story 3
ships enough of it for routing to have somewhere to route.

**Scenario:** the user pins a scope

- **Given** two scopes are loaded and I pin one in the React shell
- **When** I ask anything
- **Then** only that scope's instructions and tools are in the prompt
- **And** the other scope's tools are not offered at all

**Scenario:** nothing pinned, so cora routes

- **Given** two scopes are loaded and none is pinned
- **When** I ask a question that belongs to one of them
- **Then** the trace names the scope it routed to, and the turn runs in that scope
- **And** the Streamlit app, which has no pin, reaches the same answer by routing

**Scenario:** it asks rather than guessing

- **Given** a question that fits both scopes or neither
- **When** the turn runs
- **Then** cora asks which scope was meant, and answers with the one I choose

**Scenario:** routing is measured, not assumed

- **Given** a recorded set of questions with the scope each belongs to
- **When** the router is run over it
- **Then** a report names how often it chose the right scope
- **And** a drop below the recorded threshold fails

**Scenario:** the contract is documented as it now stands

- **Given** `docs/how-to/write-a-plugin.md`, which documents the contract this story changes
- **When** a plugin author follows it
- **Then** it says what a scope is, what `scope=None` means, and which contributions are
  always on

**Scenario:** a system-wide rule cannot be scoped away

- **Given** a `scope=None` plugin loaded beside two scopes
- **When** an injection attempt arrives in any scope, or with none pinned
- **Then** it is refused before the model is called

**Scenario:** a scoped rule applies where it belongs

- **Given** a rule contributed by a named scope
- **When** a question arrives in a different scope
- **Then** that rule does not run

### 4. A scope's documents are its own files

As a person with material in more than one field,\
I want each scope's documents kept as readable files under a place named for that scope,\
so that I can see what cora has, and a second field is a directory rather than a redesign.

**Scenario:** a citation opens onto a file

- **Given** a document ingested into a scope
- **When** its cleaned text is kept
- **Then** one Markdown file per source holds it, under that scope's directory, and the
  citation opens onto that file
- **And** nothing duplicates the text a second time

**Scenario:** a search sees one scope

- **Given** documents in two scopes
- **When** cora searches in one of them
- **Then** only that scope's sources can be retrieved or cited
- **And** `README.md` states the layout in a paragraph

### 5. cora reaches outside itself

As a person asking about something my documents cannot know,\
I want cora to call a live service and answer from what it gets back,\
so that the answer is current instead of a polite refusal.

**Scenario:** a question that needs the outside world

- **Given** a scope with a tool onto a live external service
- **When** I ask something that needs current information
- **Then** cora calls the service, the trace names the call and what it returned, and the
  answer cites it as a source
- **And** the service's text is treated as untrusted data, exactly as a document's is

**Scenario:** the service is down

- **Given** the service fails or times out
- **When** the turn runs
- **Then** one friendly message says so, the conversation is intact, and nothing is
  presented as an answer

### 6. cora acts, but only when I say so

As a person whose agent can change things,\
I want to see what it is about to do and approve it first,\
so that nothing outside cora happens without me.

**Scenario:** an effect is proposed, approved, then happens

- **Given** a scope with a tool that changes something outside cora
- **When** the model asks to call it
- **Then** cora shows what it will do and waits
- **And** nothing changes until I approve
- **And** after approval the effect happens and the trace records both

**Scenario:** declining changes nothing

- **Given** the same proposal
- **When** I decline
- **Then** nothing outside cora has changed, and the turn says what it did not do

**Scenario:** the result is mine to keep

- **Given** an approved effect that produces something — an itinerary, a training plan
- **When** it completes
- **Then** it exists as a file I keep, outside cora's own stores

### 7. What cora does with my data, said in one page

As a person uploading my own documents,\
I want one page saying what leaves my machine, what is stored and what the model is told,\
so that I can judge the privacy cost before I upload anything.

**Scenario:** the privacy and ethics page

- **Given** the docs site
- **When** a reader looks for the privacy and ethics page
- **Then** it names every place data goes — the model provider, the external services story
  5 adds, the local index, the local text, remembered facts
- **And** it says what the injection screen does and does not catch, what an effect can and
  cannot do without approval, and where the answers can be wrong
- **And** the claims match what the code does

---

## Chores

Not stories — no failing test names them — but tracked, and each is a merge of its own.

- **The test suite, 20/80** — find the fifth of the 1,247 tests carrying most of the
  protection, extend only those, archive the rest under `tests/` and delete the archive
  after submission. Membership is decided by what would go undetected, not by count.
- **An architecture note for the React shell before story 3 touches it** — the scope pin is a
  new thing on the screen, and sprint 4 shipped that frontend with no such note and said so.
- **The showcase entry**, uploaded before the review and kept current, with its link in
  `README.md` (story 1's criterion).

## Evaluation-criteria coverage

| Criterion | Where |
|---|---|
| 1 · Outcome quality | *Purpose* above; stories 5 and 6 give the agent reach and consequence, story 3 gives it focus, story 1 says what it is for |
| 2 · Learning application | *Architecture decision* above — LangGraph as a named workflow with an interrupt gate, Chroma for embeddings, OpenRouter behind the `ChatModel` port, an external API as a tool, rules and scopes as plugins |
| 3 · Ethical considerations | Story 7, standing on sprint 4's injection screen and untrusted-data handling, and on story 6's approval gate |
| 4 · Presentation | The six points: the problem (story 1), the architecture (stories 2–3), the data (story 4), evaluation (story 3's routing report), the hardest problem (stories 5–6), what is next (*Not in this sprint*) |
| 5 · Showcase submission | *Chores* — uploaded before the review, linked from `README.md` |

## Not in this sprint

Recorded with a reason, tracked in `sprint-5-feedback.md`.

- **A sub-agent inside a scope** — research and booking are the two jobs that would earn one
  (context isolation, permission isolation). It needs no new port, but it needs plugins to be
  handed a bounded-loop factory, and that contract change is bigger than the capability. The
  seam is documented; story 5's tool is where the first one would go.
- **A goal that outlives a turn** — the fourth agentic axis, and the expensive one. cora's
  checkpointer could hold an accumulating task, but nothing this sprint needs it.
- **A retrieval evaluation set** — story 3 measures the router instead, which is what the new
  headline turns on. Retrieval quality is unchanged this sprint, so a number for it would
  measure sprint 4.
- **Document removal** *(sprint-4 finding #8)* — carried again. Cheap once story 4 makes a
  source a file, which is why it is the first thing to add if the sprint runs early.
- **Stronger injection rules and a scan of document text at ingest** — the screen is still two
  regexes. Story 7 says what it does not catch rather than implying it catches everything.
- **The React page's heading outline and tab/panel wiring** — one coherent accessibility
  story, not a piece of it done off-list.
- **PostgreSQL + pgvector, second-stage reranking, richer chunk metadata** — deferred again.

## Out of scope

- **A hosted deployment.** The assignment asks for the showcase entry and a README link,
  never a running URL; `make run` and `make run-react` are how it is demonstrated.
- **A third scope.** Two prove routing and the seam; a third proves nothing further.
- **Multi-modal input, code generation, parameter-tuning studies** — cases 4, 5 and 7 are not
  the case this project answers.
- **Authentication, multi-tenancy, cost dashboards.** cora runs on the machine of the person
  whose documents it holds.
