# Sprint 5 — the capstone

The assignment (`assignment.md`) is open-ended: seven cases, and any alternative that meets
the criteria. cora is carried forward, not restarted. This file cuts the capstone into
stories with acceptance criteria and records which evaluation criterion each answers;
anything that maps to no story is out of scope. **Case 2 — an AI agent for task
automation**: case 1's retrieval is what cora does when given nothing else, not the point
of it.

## Vocabulary

The nouns this file uses, each against the class that carries it. Paths are under
`src/cora/`, and a term marked *new* is one this sprint adds.

- **Thread** — `thread_id: str`, no class of its own: the key the checkpointer and
  `ports.conversations.Conversations` both file a conversation under.
- **Turn** — `domain.conversation.Turn`, a question and the `ChatResult` it produced;
  `AgentState.turn_start` is where it begins in a thread already holding ten.
- **State** — `domain.agent_state.AgentState`, what a turn accumulates and the checkpointer
  serialises, so every key in it is a shape that costs a migration to widen.
- **Brief** — `AgentState["brief"]`, the system message `engine.steps.ScreenStep` rebuilds
  each turn and states once at the prompt's head.
- **Step** — `ports.graph.Step` as the callable, `engine.steps.*` as the implementations —
  one named part of a turn with a single responsibility.
- **Trace** — `AgentState["trace"]`, a list of `domain.trace.TraceStep`: `StepEntered`,
  `ModelDecision`, `ToolUse`, `MemoryUnread` today, nesting from story 4 — drawn on the
  screen from story 10.
- **Plugin** — `ports.plugin.Plugin`, a frozen record today; becomes `extend(cora: Host)` in
  story 4.
- **Host** *(new, story 4)* — the port a plugin is handed at load: cora's own parts, and the
  calls that register.
- **Registration** *(new, story 4)* — one thing a plugin contributed, carrying — from
  story 5 — the scope it lives in; replaces the four fields of `Plugin`.
- **Scope** *(new, story 5)* — one field on a registration, naming the field a turn runs in
  and the lifetime of everything registered under it; `None` means system-wide.
- **Tool** — `ports.plugin.Tool`, asked for as a `ToolCall` and answered by a `ToolResult`.
- **Rule** — was `ports.plugin.ValidationRule`; gone in story 5, where screening became a
  handler on the *screen* event and cora's own rules became system-wide subscribers.
- **Handler** *(new, story 5)* — a registration subscribed to a named point in the turn,
  returning an amendment or a refusal — never a pause, which is the gate's privilege
  alone. Instructions stayed a registration: they are a string, and the brief's headings
  are composed from them.
- **Effect** *(new, story 11)* — a tool call that changes something outside cora, and so
  waits for approval before it runs.
- **Approval** *(new, story 11)* — a yes or no bound to one proposed call, checkpointed;
  distinct from `domain.decision.Decision`, which answers "which fact is current".
- **Pause** — `domain.decision.Pending` raised as `TurnPaused`, a turn stopped mid-flight
  with what it needs settled.
- **Pin** *(new, story 6)* — a key in `AgentState` holding the scope a user fixed a thread
  to: set by the user and by nobody else, at whatever turn the conversation turns out to
  have a field, and never set twice. It survives a reload, and it is what a routed scope is
  not — a decision about the conversation rather than a reading of one question.
- **Citation** — `domain.citations.Citation`, offsets into stored text today, widening to a
  source with kinds in story 9.
- **Document** — one source behind `ports.documents.Documents`, chunked into
  `domain.chunk.Chunk` and retrieved as `ports.retrieval.RetrievedChunk`.
- **Memory** — `ports.memory.Memory`, holding `Fact`s about the person, system-wide across
  every thread and scope.
- **Session** — `domain.conversation.Session`, a row in `Conversations.sessions()`: a thread
  id and the question that opened it.

## Purpose (criterion 1 · outcome quality)

**cora is an agent you chat with, and everything it knows and can do arrives as a plugin.**
The core runs a turn and screens what comes in; a plugin gives it a field, tools, rules and
a say in every step. With nothing loaded it still answers: it searches its documents,
remembers what it is told, asks when it cannot tell, and cites what it used.

**What a plugin contributes** — moments in a turn, not fields on a record:

- **things cora can do** — a tool, named and schema'd, the model may call
- **what cora is** — instructions heading its brief while the plugin's scope is active
- **what it will not accept** — a rule that refuses an input before any model call
- **a say in the turn** — a handler on a named step: amend what goes to the model, refuse a
  tool call before it runs, wrap what comes back
- **cora's own parts** — retrieval, memory, the model itself, so a plugin can run a bounded
  loop of its own without cora growing a feature for it

**Who it is for.** People who extend the tools they work in, and will point an agent at
their own field themselves. That makes the plugin contract the product surface, and
`docs/how-to/write-a-plugin.md` part of the product.

**What the core keeps is what a plugin cannot replace**, so it keeps as little as it can:
named steps, a registry, events, an approval gate. What cora deliberately lacks is stated as
a decision rather than left to be discovered.

**cora ships pointed at fields that are not code** — a coach, a trip, a lab notebook — but
nothing in the contract forbids the other subject, and that is the test of whether the
contract is real: a tool that edits a file is a tool with an effect, and the gate's shape
must not foreclose it — real code work proposes many effects in one turn, so approving it
is a wider approval, not a core change. A shell is another frontend over the same `Agent`.
Both are later sprints; if either turns out to need a core change, the contract was wrong.

**Three plugins ship**: **security** (rules only, system-wide), **fitness** and **travel**.
Two scopes, not one — the second proves a scope is a plugin and not a fork, and one scope
leaves routing nothing to choose between.

## Architecture decision (criterion 2 · learning application)

LangGraph, hexagonal: the domain holds the state shape, the engine holds the steps as plain
functions, and technology binds only in the adapters — the domain, ports, engine and app
import none of it, and the architecture guard enforces that split per layer. Eight
decisions, and the first three are the sprint.

- **A plugin is handed cora; it does not fill in a form.** `PLUGIN = Plugin(name,
  instructions, tools, validation_rules)` is a frozen record, so a fifth kind of
  contribution is a field on a core dataclass and a sixth is another. It becomes
  `extend(cora: Host) -> None`, registering what it has, and the host is what hands over
  cora's retrieval, memory, model, logger and the configuration named for that plugin.
  Story 4.

- **The four fields were three hooks all along.** A rule fires before a turn starts,
  instructions before the model is called, tools are a registry the model reads — moments,
  hard-coded because there was one of each. Story 3 names the steps, story 5 gives them
  subscribers, and cora's own screen becomes a subscriber too: a mechanism the core does
  not itself eat is one nobody can trust. Handlers compose in a stated order — cora's
  screen first, then plugins as loaded — and amendments chain, each seeing what the one
  before it returned; the gate stands after them all, a step of its own rather than a
  handler. Story 5.

- **The contract is versioned and small, because it is now someone else's.**
  `cora.ports.plugin` and `Host` are public; everything else may move. A plugin may declare
  the version it was written against, and a mismatch is a refusal that names the problem
  rather than an `AttributeError` mid-turn. Cheapest to write now, most expensive to
  retrofit after someone has published against it. Story 7.

- **A plugin is installed, not forked — and cora says what it loaded.** Two sources in
  precedence order: `CORA_PLUGINS`, and a `.py` file in `./.cora/plugins/` — entry-point
  discovery waits for the sprint that has an external author. Beside them, a listing of
  what is loaded, from where, and what each contributed — without it, two plugins in
  disagreement is an unanswerable question. Story 7.

- **The turn is a named sequence with the loop inside it.** `prepare → model ⇄ tools`
  becomes *screen → route → focus → work → answer*, each step with one responsibility, its
  own place in the trace and its own subscribers. Story 3 delivers *screen → work →
  answer*; story 6 inserts *route* and *focus*. The model's freedom lives in *work* and
  nowhere else.

- **A scope is the lifetime of a registration.** One field on every registration, not a
  second plugin type: `scope=None` is system-wide — always in the prompt, always callable,
  always enforced, which is why the injection screen lives there, why no scope can switch it
  off, and why the fitness plugin's medical filter moves there. Safety is not a domain
  concern. The active tools are a filtered view of one registry — the active scope plus the
  system-wide — and widening that set is a supported move, not a second code path. Stories
  5 and 6.

- **A scope owns its documents.** Cleaned text moves from `adapters/sqlite_documents.py` to
  one Markdown file per source, under a directory named for its scope, behind the
  `Documents` port that already exists; the index keeps embeddings and offsets and reads the
  text back from the file. That answers the reviewer's two store findings at once. Threads
  and remembered facts stay in SQLite, and memory stays system-wide — one person, both
  scopes. Story 8.

- **An effect is gated by the interrupt that already exists, and the gate is the core's.** A
  tool that changes something outside cora says what it is about to do and waits. The gate
  stands at the *tool-call* point but is not a handler: it pauses the turn, which no plugin
  may do, so it is a privileged core step — and it settles every approval *ahead* of the
  round's execution, the same move the ask step already makes, because a resumed step
  replays from its first line and an effect must never run twice. It is deliberately baked
  in, because cora's effects land in a field its user did not write code for, running a
  plugin they very likely did not read: a plugin cannot unsubscribe it. Story 11.

### Shapes the stories must honour

Each is a *shape* rather than a feature, and `AgentState`'s types are serialised into every
persisted thread — so widening one later is a lock bump and a migration, while getting it
right now costs nothing.

- **The registry is one list.** A tool, a rule and an instruction differ in what the value
  *is*, not in how long it lives, so the scope rule, the listing, the collision check and
  the trace are each written once.
- **A handler returns a decision; it never mutates.** Frozen values in, a refusal or an
  amendment out. A hook that can write the state is a hole in the hexagon, and a handler
  that returns stays testable as a function.
- **A failing handler fails closed for a rule, open for an observer — and an amender that
  raises is dropped like an observer.** A refusing rule that raises must not become an
  accepted input; a lost amendment must not become a lost turn. Either way the trace names
  the plugin.
- **Routing yields the active scope*s*.** One scope is the degenerate case of a set; with a
  single value, a question spanning two becomes a change to the state shape, the prompt, the
  tool filter, the trace and every stored thread.
- **No plugin loaded *is* a scope.** Its documents need a directory like any other's, and a
  default scope gives one code path where "unscoped" would give a switch.
- **The trace nests.** A plugin holding the model can run a loop of its own, and a tool that
  does must show its nested work, or "watch what it did" goes shallow where it matters most.
- **A sub-agent may read, never act.** A delegated loop is offered read-only tools, so an
  effect and a stop-to-ask stay in the outer turn where the gate already is. Without that
  rule an interrupt has to travel up through a checkpointed inner loop and back down, which
  is a harder problem than the capability is worth.
- **A citation's source has kinds.** Story 9 cites a live service, which has no document and
  no offsets, so `Citation` widens once to a source with kinds — a stored span, a fetched
  result — and a third kind later is a new case rather than a new shape.
- **The pin belongs to the conversation.** It goes in `AgentState` and is checkpointed, so a
  reopened thread reopens in its scope; frontend session state would lose it on reload.
- **A turn may stop more than once, and every stop comes before the round runs.**
  The recursion limit needs no resizing for a stop: it is spent one `run` at a time, and a
  stop ends the run it was in, so the resumed one pays for none of the steps before the
  loop — measured, a stopping walk is always cheaper than one that never stops. What does
  need sizing is a walk with more *steps* in it, which `recursion_limit_for` already takes.
  And because a resumed step replays from its first line, a
  stop in the middle of a half-run round would re-run what already ran: approvals are
  settled ahead of execution, never mid-round.
- **An approval is its own checkpointed type, bound to one call.** Sprint 4's `Decision`
  works for one effect and breaks on the second, or on an argument the user wants to edit
  before approving.

**Nothing is carried over.** No migration in either direction: a store written before this
sprint is deleted and re-ingested, and the two existing plugins are rewritten to the new
contract with no shim keeping the old shape alive — the travel plugin is born to it in
story 6. These shapes are decided for what comes *after* this sprint, not to protect what
came before it.

---

## Stories

Numbered in merge order, with one exception: story 8 merges after story 11, so the reach
the review asked for is never queued behind storage polish. Each becomes an OpenSpec
change under `openspec/changes/`, and the story moves into it when it is opened — into
the change's delta spec, or into its proposal where the subject is a written page and
there is no delta. It goes from this file as it does, heading and all: what is left below
is the stories no change holds yet, which is why the numbering starts where it does.

Stories 4, 5 and 7 are the harness, 9, 10 and 11 are the reach the review asked for, and
1, 2 and 12 are how it is read. **Twelve stories, and none of them is designated as the
one that gives.** Story 2's removal was, while it was a freeze that could wait. Deleting
the second frontend outright in position two spends that slack early, and buys back every
core change of stories 4 and 5 that would have had to keep a dead app compiling. Routing
was the other cut considered — a pin alone proves a scope — and it stays: it carries
criterion 4's evaluation number, and one scope leaves nothing to route between, so cutting
it would take the measurement with it. If the sprint runs long, the sprint runs long, and
what gives is argued then against *Not in this sprint* rather than decided here while it
is cheap to be brave.

### 7. A plugin is installed, not forked, and cora says what it loaded

As someone who wrote a plugin for my own field,\
I want to install it or drop it in a folder and have cora find it,\
so that using it does not mean forking cora.

**Scenario:** a named module is enough

- **Given** a plugin module named in `CORA_PLUGINS`, its code living outside this repository
- **When** cora starts
- **Then** it is loaded
- **And** nothing under `src/cora/` names it

**Scenario:** a file is enough

- **Given** a single `.py` file in `./.cora/plugins/`
- **When** cora starts
- **Then** it is loaded with no packaging at all, and the listing says where it came from

**Scenario:** cora says what is loaded

- **Given** several plugins from different sources
- **When** I ask cora what it has
- **Then** each one is listed with its source, its scope, its tools, its rules and the steps
  it subscribes to
- **And** every system-wide registration is flagged as such — a tool callable in every
  scope is a visible act, not a quiet field
- **And** the same listing is on the screen, not only in a terminal

**Scenario:** the contract has a version and says so

- **Given** a plugin declaring a contract version cora does not support
- **When** it is loaded
- **Then** the refusal says which version it wants and which cora offers
- **And** `docs/how-to/write-a-plugin.md` names what is public and what may move — a
  compatibility policy waits for the first author it would bind

**Scenario:** a plugin is a distribution, not a fork

- **Given** the contract, complete
- **When** the travel plugin is read back against it
- **Then** it is a distribution and nothing more, and a guard asserts that the core names no
  plugin and no scope

### 8. A scope's documents are its own files

As a person with material in more than one field,\
I want each scope's documents kept as readable files under a place named for that scope,\
so that I can see what cora has, and a second field is a directory rather than a redesign.

**Scenario:** a citation opens onto a file

- **Given** a document ingested into a scope
- **When** its cleaned text is kept
- **Then** one Markdown file per source holds it, under that scope's directory, and the
  citation opens onto that file
- **And** nothing duplicates the text a second time — the index keeps embeddings and
  offsets, and reads a chunk's text from the file

**Scenario:** a search sees one scope

- **Given** documents in two scopes
- **When** cora searches in one of them
- **Then** only the active scope's sources can be retrieved or cited
- **And** `README.md` states the layout in a paragraph

**Scenario:** an upload with no scope has a home

- **Given** a document uploaded with no scope chosen
- **When** it is ingested
- **Then** it lands in the default scope's directory, and an unscoped search can retrieve
  it — the default scope is a scope like any other

It merges after story 11: nothing in stories 9–11 reads these files, so the reach never
waits on this polish.

### 9. cora reaches outside itself

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

**Scenario:** the plugin holds its own key

- **Given** the service needs a credential
- **When** the plugin asks the host for its configuration
- **Then** it gets the slice named for it, from the environment, and the key is in no log
  and no trace

The travel plugin needs an HTTP client, so the architecture guard's technology allow-list
for the plugins widens by that one name — a guard edit this story owns, made in the open.

### 10. cora sends a researcher and reads the report

As a person asking something that takes several lookups,\
I want cora to delegate the digging and come back with one answer,\
so that a broad question is answered without the searching itself filling the conversation.

**Scenario:** a broad question is researched, not answered in one pass

- **Given** the travel scope, with its documents and the live-service tool story 9 added
- **When** I ask something that needs several lookups — three days somewhere, what is open,
  what the weather will be
- **Then** a tool runs a bounded loop of its own and the answer rests on what it found
- **And** the trace shows the researcher's steps nested under the call that started it
- **And** the conversation carries the report, not every lookup that produced it

**Scenario:** a researcher reads and does not act

- **Given** a scope holding both the researcher and a tool marked as an effect — the mark
  is just a field on a registration; story 11 builds its gate, and travel's real effect
  arrives with it
- **When** the researcher runs
- **Then** only read-only tools are offered to it, and it can neither propose an effect nor
  stop to ask
- **And** a guard asserts that rule, because it is what keeps a nested turn from needing a
  nested approval

**Scenario:** the fan-out has a ceiling

- **Given** a question that could be split many ways
- **When** the researcher runs
- **Then** it makes at most the configured number of rounds, and the report says so when it
  stopped early rather than presenting a partial answer as a whole one

**Scenario:** it is a plugin, not a feature

- **Given** the researcher, working
- **When** this story's diff is read
- **Then** nothing under `src/cora/` was changed to allow it, beyond the shell learning to
  draw a nested step

It lands after story 9 because a researcher with nothing to research is a loop, and it is
where story 4's claim stops being a test and becomes something a user watches. **The React
shell learns to draw nesting here** — story 4 asserts nested steps exist in the trace and
nobody draws them yet, which is this story's one cost outside the plugin.

### 11. cora acts, but only when I say so

As a person whose agent can change things,\
I want to see what it is about to do and approve it first,\
so that no effect cora is asked for happens without me.

**Scenario:** an effect is proposed, approved, then happens

- **Given** a scope with a tool that changes something outside cora
- **When** the model asks to call it
- **Then** cora shows what it will do and waits
- **And** nothing changes until I approve
- **And** after approval the effect happens and the trace records both

**Scenario:** two effects in one turn, and nothing runs twice

- **Given** a turn in which the model proposes two effects
- **When** I approve the first and then the second
- **Then** each ran exactly once — the approvals were settled before the round executed, so
  resuming never replays an effect that already ran

**Scenario:** declining changes nothing

- **Given** the same proposal
- **When** I decline
- **Then** nothing outside cora has changed, and the turn says what it did not do

**Scenario:** the gate is cora's, not the plugin's

- **Given** a plugin that marks a tool as having an effect
- **When** that tool is called
- **Then** the gate runs — a privileged core step at the tool-call point that a plugin can
  neither unsubscribe nor imitate, since no handler may pause a turn
- **And** the gate covers what is declared to cora: a plugin's own code running past it is
  the trust decision story 12 names, not a hole in the gate

**Scenario:** the result is mine to keep

- **Given** an approved effect that produces something — an itinerary, a training plan
- **When** it completes
- **Then** it exists as a file under the output location the app is configured with, outside
  cora's own stores, and `README.md` says where that is

### 12. What cora does with my data, and what a plugin costs in trust

As a person uploading my own documents and loading someone else's plugin,\
I want one page saying what leaves my machine, what is stored, what the model is told and
what a plugin may do,\
so that I can judge both costs before I take either.

**Scenario:** the privacy and ethics page

- **Given** the docs site
- **When** a reader looks for the privacy and ethics page
- **Then** it names every place data goes — the model provider, the external services story
  9 adds, the local index, the local text, remembered facts
- **And** it says what the injection screen does and does not catch, what an effect can and
  cannot do without approval, and where the answers can be wrong
- **And** the claims match what the code does

**Scenario:** what loading a plugin costs in trust

- **Given** a reader deciding whether to load a plugin someone else wrote
- **When** they look for what it may do
- **Then** the page says a loaded plugin is arbitrary code running with their own
  permissions — instructions the model follows, tools it may call, handlers that can refuse
  or amend, and effects outside cora — and that this is true of every harness of this kind
- **And** it names what cora enforces whatever a plugin does: the approval gate before an
  effect, retrieved and fetched text handled as untrusted data, output confined to the
  configured directory, and the tool names a plugin may not take
- **And** it says what cora does *not* enforce: no sandbox, no network restriction, no
  review of what a plugin's instructions tell the model

## Chores

Not stories — no failing test names them — but tracked, and each is a merge of its own.

- **The test suite, 20/80** — find the fifth of the suite carrying most of the protection.
  Story 2 took the Streamlit suite out of the question by deleting it, so what is weighed
  is what is left. Extend only what earns it, archive the rest under `tests/` and delete
  the archive after submission. Membership is decided by what would go undetected, not by
  count.
- **An architecture note for the React shell before story 6 touches it** — the scope pin and
  the plugin listing are both new things on the screen, and sprint 4 shipped that frontend
  with no such note and said so.
- **The showcase entry**, uploaded before the review and kept current, with its link in
  `README.md` (story 1's criterion).

## Evaluation-criteria coverage

| Criterion | Where |
|---|---|
| 1 · Outcome quality | *Purpose* above; stories 4, 5 and 7 make the plugin contract the product — a stranger can extend cora without forking it — stories 9, 10 and 11 give the agent reach, delegation and consequence, story 6 gives it focus, story 1 says what it is for, and story 2 keeps one frontend growing so there is one to judge it by |
| 2 · Learning application | *Architecture decision* above — LangGraph as a named workflow with subscribable steps and an interrupt gate, Chroma for embeddings, OpenRouter behind the `ChatModel` port, an external API as a tool, a delegated loop written as a plugin, and a plugin contract that is the sprint's own design work |
| 3 · Ethical considerations | Story 12, standing on sprint 4's injection screen and untrusted-data handling, on story 11's approval gate, and on story 5's rule that a system-wide screen cannot be scoped away |
| 4 · Presentation | The six points: the problem (story 1), the architecture (stories 3–7), the data (story 8), evaluation (story 6's routing report), the hardest problem (stories 4–5, the contract inversion, and story 10 standing on it), what is next (*Not in this sprint*) |
| 5 · Showcase submission | *Chores* — uploaded before the review, linked from `README.md` |

## Not in this sprint

Recorded with a reason. The items carried from sprint 4 are tracked in
`sprint-5-feedback.md`; the rest are this sprint's own deferrals, and this list is their
record.

- **A sub-agent that acts, or one that stops to ask.** Story 10's researcher reads and
  reports; an inner loop that proposes an effect or asks a question needs an interrupt to
  travel up through a checkpointed subgraph and back down, and that is a bigger problem than
  the capability it buys. Booking is the job that would earn one.
- **A plugin depending on another plugin, overriding another's tool, or ordering itself
  against one.** Load order is the only precedence there is, and it is the order the sources
  were read in. All three are real needs of a mature harness and none is needed by three
  plugins; each is additive on `Host` when it is.
- **Entry-point discovery.** A plugin distribution announcing itself through a
  `cora.plugins` group serves an author who does not exist yet; `CORA_PLUGINS` and the
  plugins folder already load code from outside the repository. Additive on the loader the
  day an external author appears.
- **Splitting what a scope fuses.** One scope field decides what cora is told, what it may
  call and what it may read, in lockstep; a turn that wants one scope's documents without
  its persona and tools cannot say so. Splitting read-scope from act-scope is a later
  axis, and the set-shaped routing is the escape hatch until then.
- **A sandbox, or any restriction on what a plugin's code may do.** A plugin runs with the
  user's full permissions, which is true of every harness of this kind, and story 12 says so
  rather than implying otherwise. A capability-restricted plugin is a project, not a story.
- **Commands, shortcuts and screen elements from a plugin.** A plugin could reach the whole
  screen; this sprint's reach the turn. The frontend seam is not the one this sprint is
  proving, and widening two seams at once is how neither gets proved. A second frontend — a
  shell, a TUI — is the same deferral seen from the other side: it is a caller of `Agent`,
  so it costs a frontend and not a contract.
- **A goal that outlives a turn** — the fourth agentic axis, and the expensive one. cora's
  checkpointer could hold an accumulating task, but nothing this sprint needs it.
- **A retrieval evaluation set** — story 6 measures the router instead, which is what the
  new headline turns on. Retrieval quality is unchanged this sprint, so a number for it
  would measure sprint 4.
- **Document removal** *(sprint-4 finding #8)* — carried again. Cheap once story 8 makes a
  source a file, which is why it is the first thing to add if the sprint runs early.
- **Stronger injection rules and a scan of document text at ingest** — the screen is still
  two regexes. Story 12 says what it does not catch rather than implying it catches
  everything.
- **The React page's heading outline and tab/panel wiring** — one coherent accessibility
  story, not a piece of it done off-list.
- **PostgreSQL + pgvector, second-stage reranking, richer chunk metadata** — deferred again.

## Out of scope

- **Code as cora's subject, this sprint.** Nothing ships that reads a repository, edits a
  file or runs a command, and no story asks for it — the fields on offer are fitness and
  travel. This is a cut, not a boundary: a plugin whose subject is code, and a shell
  frontend beside the React one, are both later sprints that the contract is meant to
  accommodate without a core change. The extension model is the point; the subject it is
  pointed at now is not.
- **A hosted deployment.** The assignment asks for the showcase entry and a README link,
  never a running URL; `make run` is how it is demonstrated.
- **A third scope.** Two prove routing and the seam; a third proves nothing further.
- **A plugin registry or directory.** A named module and a folder are discovery; a place to
  browse other people's plugins is a website, and there are no other people yet.
- **Multi-modal input, code generation, parameter-tuning studies** — cases 4, 5 and 7 are
  not the case this project answers.
- **Authentication, multi-tenancy, cost dashboards.** cora runs on the machine of the person
  whose documents it holds.
