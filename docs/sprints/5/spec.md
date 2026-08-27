# Sprint 5 — the capstone

The assignment (`assignment.md`) is open-ended: seven cases, and any alternative that meets
the criteria. cora is carried forward, not restarted. This file cuts the capstone into
stories with acceptance criteria and records which evaluation criterion each one answers.
Anything that maps to no story here is out of scope.

**Case 2 — an AI agent for task automation.** Case 1's retrieval is what cora does when it
is given nothing else, not the point of it.


## Purpose (criterion 1 · outcome quality)

**cora is an agent you chat with, and everything it knows and can do arrives as a plugin.**
The core runs a turn and screens what comes in; a plugin gives it a field, tools, rules and
a say in every step. With nothing loaded it still answers: it searches its documents,
remembers what it is told, asks when it cannot tell, and cites what it used. 



**What a plugin may contribute.** Not a list of fields, which is the shape this sprint
leaves behind, but a list of *moments*:

- **things cora can do** — a tool, named and schema'd, the model may call
- **what cora is** — instructions that head its brief while the plugin's scope is active
- **what it will not accept** — a rule that refuses an input before any model call
- **a say in the turn** — a handler on a named step, which may amend what goes to the model,
  refuse a tool call before it runs, or wrap what comes back
- **its own use of cora's parts** — retrieval, memory, the model itself, so a plugin can run
  a bounded loop of its own without cora growing a feature for it

**Target users.** People who extend the tools they work in. They want an agent pointed
at *their* field, and they will point it themselves. That makes the plugin contract the
product surface, and `docs/how-to/write-a-plugin.md` part of the product rather than
documentation of it.

**The stance.** A harness people extend is a different product from an agent with a plugin
folder, and the difference is what the core refuses to own. cora ships the parts a turn is
made of — named steps, a registry, events, an approval gate — and leaves what is built from
them to whoever needs it. Anything baked in is something a plugin author cannot replace, so
the core stays the smallest thing that can run a turn and screen what comes in, and what it
does *not* have is stated as a decision rather than left to be discovered. Where cora keeps
something for itself anyway, that is named where it happens rather than left to be noticed.

**cora does not ship as a coding agent, and the difference is what it ships with, not what
it permits.** A harness of this kind is usually built to extend an agent that touches code;
cora ships pointed at fields that are not — a coach, a trip, a lab notebook, bird sightings
— and the reach it needs for those. But nothing in the contract this sprint builds forbids
the other subject, and that is the test of whether the contract is real: a tool that edits a
file is a tool with an effect, and it passes the same approval gate as any other, so
*coding* is a plugin someone writes rather than a different product. A shell is likewise a
**frontend** — another caller of the same `Agent`, beside the React shell — not a change to
the core. Both are later sprints and neither is a rewrite; if either turns out to need one,
the contract was wrong. The three shipped plugins are the demonstration, not the point:
**security** (rules only, system-wide), **fitness** and **travel** (two scopes). Two scopes,
not one: the second is the proof that a scope is a plugin and not a fork — it is written
without touching the core — and it is what makes routing worth having, since one scope
leaves nothing to choose between.

## Architecture decision (criterion 2 · learning application)

The agent stays on **LangGraph**, hexagonal: the domain holds the state shape, the engine
holds the steps as plain functions, and only `adapters/langgraph_runner.py` imports the
framework — the architecture guard enforces it. Eight decisions are this sprint's, and the
first three are the sprint.

- **A plugin is handed cora; it does not fill in a form.** Today a plugin module defines
  `PLUGIN = Plugin(name, instructions, tools, validation_rules)` — a frozen record with four
  slots, so a fifth kind of contribution is a field on a core dataclass and a sixth is
  another. It becomes a function the loader calls with a host: `extend(cora: Host) -> None`,
  registering what it has. New kinds of contribution then arrive as a method on `Host`,
  additively, and most arrive as nothing at all — see the next decision. The host is also
  what hands a plugin cora's own parts: its retrieval, its memory, its model, its logger,
  and the slice of configuration named for that plugin. Story 4.

- **The four fields were three hooks all along.** `validation_rules` fires before a turn
  starts, `instructions` fires before the model is called, `tools` is a registry the model
  reads — those are moments in a turn, hard-coded because there was only one of each. The
  turn gets named steps in story 3 and those steps get subscribers in story 5, so a rule and
  an instruction become handlers like any other, and cora's own screen and approval gate
  become subscribers to the same events a plugin uses. A mechanism the core does not itself
  eat is a mechanism nobody can trust. Story 5.

- **The contract is versioned and small, because it is now someone else's.**
  `cora.ports.plugin` and `Host` are the public surface; everything else is cora's
  business and may move. A contract version ships beside them, a plugin may declare the
  one it was written against, and a mismatch is a refusal that names the problem rather
  than an `AttributeError` three steps into a turn. This is the cheapest paragraph in
  the sprint to write now and the most expensive to retrofit after someone has published
  against it. Story 7.

- **A plugin comes from anywhere, and cora says what it loaded.** Three sources, in
  precedence order: `CORA_PLUGINS`, which is explicit and ordered and stays the test hook;
  entry points in the `cora.plugins` group, which is how an installed distribution announces
  itself; and `~/.cora/plugins/*.py` beside `./.cora/plugins/*.py`, which is a file someone
  drops in with no packaging at all. Beside it, the thing no harness can do without: a
  listing of what is loaded, where it came from and what each one contributed, without which
  two plugins in disagreement is an unanswerable question. Story 7.

- **The turn becomes a named sequence, with the loop inside it.** Today `prepare → model ⇄
  tools` is one ReAct loop where a single model call decides everything. It becomes
  *screen → route → focus → work → answer*, each step with one responsibility, its own place
  in the trace and its own subscribers. Story 3 delivers *screen → work → answer*; story 6
  inserts *route* and *focus* between them.

- **A scope is the lifetime of a registration, and the active set is state.** One field on
  every registration, not a second plugin type: `scope=None` is system-wide — always in the
  prompt, always callable, always enforced, which is why the injection screen lives there
  and no scope can switch it off — and a named scope is in play only while it is active. The
  *active* tools are then a filtered view of one registry rather than a
  differently-assembled prompt, which is what settles the question this file left open: the
  default is the active scope plus the system-wide, and widening that set is a supported
  move a plugin or the user can make, not a second code path. Stories 5 and 6.

- **A scope owns its documents.** The cleaned text a citation opens onto moves from
  `adapters/sqlite_documents.py` to one Markdown file per source, under a directory named
  for its scope, behind the `Documents` port that already exists — and the index stops
  keeping a copy of chunk text, holding embeddings and offsets and reading the text back
  from the file. That answers the reviewer's two store findings together: the duplication
  goes, and a second domain's layout becomes a directory anyone can read. Threads and
  remembered facts stay in SQLite; they are not duplicated raw data. Memory stays
  system-wide — one person, both scopes. Story 8.

- **An effect is gated by the interrupt that already exists, and the gate is the core's.**
  Sprint 4 built `interrupt` so cora could stop and ask which of two facts was current. A
  tool that changes something outside cora stops the same way: it says what it is about to
  do and waits. The gate is a handler on the *tool-call* event — the same one a plugin may
  subscribe to — so it is the core's own use of the mechanism story 5 adds. It is also the
  one thing this sprint deliberately bakes in against its own rule, and the reason is the
  audience: a harness for developers can leave the gate to whoever wants one, because its
  users took the risk knowingly and can write it themselves, while cora's effects land in a
  field its user did not write code for, running a plugin they very likely did not read. So
  a plugin cannot unsubscribe it. Everywhere else the core stays out of the way; here it
  does not, on purpose. Story 10.

### Shapes the stories must honour

Ten constraints, decided here because each one is a *shape* rather than a feature.
`AgentState`'s types are enumerated in `CHECKPOINTED_DATA`, and the trace's step kinds join
them in `checkpointed_types()`, so both are serialised into every persisted thread: widening
one later is a lock bump and a migration, while getting it right now costs nothing.

- **A registration is a value with a scope, and the registry is one list.** Not four fields
  and not four registries. What differs between a tool, a rule and an instruction is what
  the value *is*, not how long it lives or who may look at it, so the scope rule, the
  listing, the collision check and the trace are each written once.
- **A handler returns a decision; it never mutates.** A subscriber is handed frozen values
  and returns what it wants changed — a refusal with a reason, an amended brief, a wrapped
  result — or nothing. The usual shape for this is a mutable context the handler reaches
  into, and cora cannot have it: the state shape belongs to the domain, and a hook that can
  write it is a hole in the hexagon. Returning a decision also keeps a handler testable as a
  function, which is what the Detroit-school tests need.
- **A handler that fails, fails closed for a rule and open for an observer.** A refusing
  rule that raises must not become an accepted input — the security plugin is the case that
  matters. An observer that raises is reported against its plugin and skipped. Either way
  the trace names the plugin, because "it went wrong somewhere" is the failure mode a
  harness cannot have.
- **Routing yields the active scope*s*, not the active scope.** One scope is the degenerate
  case of a set. A question that spans two scopes is the obvious next ask, and with a set it
  is a later routing rule; with a single value it is a change to the state shape, the prompt
  assembly, the tool filter, the trace and every thread already stored.
- **No plugin loaded *is* a scope.** cora with nothing loaded is agentic RAG over documents,
  and those documents need a directory like any other scope's. A default scope gives one
  code path and one layout rule; "unscoped documents" would give a switch, which is the
  thing the project's north star forbids.
- **The trace has room for a child step, and now something will nest.** Once a plugin holds
  the model it can run a loop of its own, and a tool that runs one must be able to *show*
  its nested work, or cora's "watch what it did" claim goes shallow exactly where the
  interesting work is. This stops being a hedge against a deferred feature and becomes a
  requirement of the contract.
- **A citation's source has kinds; it is not always a document.** Today a `Citation` is
  offsets into stored text, and `Citation` is checkpointed. Story 9 cites a live service,
  which has neither a document nor offsets. The type widens once, when story 9 lands, and it
  widens to a source *with kinds* — a span of a stored document, a fetched result — so that
  a third kind later is a new case rather than a new shape.
- **The pin belongs to the conversation, not to the browser tab.** A pinned scope goes in
  `AgentState` and is checkpointed, so reopening a thread reopens it in the scope it was
  held in, and the trace can say which scope a turn ran in whether it was pinned or routed.
  Session state in the frontend would lose it on reload and leave the thread's own record
  incomplete.
- **A turn may now stop more than once.** Sprint 4 set `ASKS_PER_TURN = 1` and sized the
  graph's recursion limit from it. A turn can now stop to ask which scope *and* to approve
  an effect, and a turn proposing two effects stops three times. The budget is resized as
  the stops are added, or a legitimate turn trips the runaway guard.
- **An approval is its own checkpointed type, bound to one call.** Sprint 4's `interrupt`
  carries a `Decision` of labelled options for "which fact is current". Squeezing "may I
  write this file" into that shape works for one effect and breaks on the second — two
  effects in one turn, or an argument the user wants to edit before approving, both need the
  approval bound to a specific call.

**Nothing is carried over.** No migration, in either direction: cora is an MVP with no
deployment, so a store written before this sprint — its threads, its index, its kept text —
is deleted and re-ingested rather than converted. The same goes for the plugin contract: the
three shipped plugins are rewritten to the new one in the story that introduces it, and no
compatibility shim keeps the old shape alive. The shapes above are decided for what comes
*after* this sprint, not to protect what came before it.

**One behaviour change this implies:** the fitness plugin's medical filter becomes
fitness-only unless it moves, so a medical question asked in the travel scope, or with
nothing pinned, would meet no filter. The rule is right and its *home* was wrong — a screen
that must always apply belongs in a system-wide plugin beside the injection screen, not
inside a domain. Story 5 moves it there. Safety is not a domain concern. ---

## Stories

Numbered in merge order. Each becomes an OpenSpec change under `openspec/changes/`, and its
text moves into that change's `proposal.md` when it is opened — this file then keeps the
heading and the link.

Stories 4, 5 and 7 are the harness; 9 and 10 are the reach the review asked for; 1, 2 and 11
are how it is read. **Eleven stories, and none of them is a candidate for a late cut.**
Routing was the one considered — a pin alone proves a scope — and it stays: it carries
criterion 4's evaluation number, and one scope leaves nothing to route between, so cutting it
would take the measurement with it and leave the second scope proving only that a plugin
loads. If the sprint runs long, the sprint runs long; what gives is argued then, against
*Not in this sprint*, rather than decided here while it is cheap to be brave.

### 1. A reader learns what cora is for before anything else

As a person who lands on the repository,\
I want the first screen to tell me what problem this solves and for whom,\
so that I can decide whether it is for me without reading the code.

**Scenario:** the front door explains itself

- **Given** `README.md` as the front door
- **When** someone who has never seen cora reads its first screen
- **Then** they can say what problem it solves, who it is for and how it works
- **And** they can see what writing a plugin of their own involves, and where the how-to is
- **And** the showcase entry is linked near the top

**Scenario:** what cora does not have, said on purpose

- **Given** the README's first screen
- **When** a reader looks for what is missing
- **Then** a short block names it as chosen, with the reason standing beside each rather
  than after the list:
  - **no sandbox around a plugin** — a plugin is code you chose to install, like any package
    you `uv add`, and saying so plainly is safer than a gate that implies a containment cora
    does not have
  - **no registry to browse** — entry points and a folder are discovery; somewhere to find
    other people's plugins is a website, and there are no other people yet
  - **no subject but the two shipped** — a subject *is* a plugin, so a third proves nothing
    the second did not
  - **no goal that outlives a turn** — cora answers and stops; a task that accumulates is
    the next axis, not this one
- **And** it reads as a boundary rather than an apology, which is what stops a reader
  mistaking a decision for a gap

**Scenario:** the one sentence says what cora now is

- **Given** the tagline guard, which holds `README.md`, `docs/index.md`, `pyproject.toml`,
  `mkdocs.yml` and `CLAUDE.md` to one sentence
- **When** the sentence changes to the *Purpose* section's
- **Then** every copy changes with it and the guard stays green

Written day one, before the code — the retrospective names cutting it last as the cause of
the reviewer seeing it. The sentence is rewritten here and the rest of the README follows
the sprint, since stories 4 to 7 change what there is to describe.

### 2. cora has one frontend

As someone who runs cora,\
I want one frontend rather than two,\
so that a change to the screen is made once and the other one cannot fall behind.

**Scenario:** the Streamlit app is gone

- **Given** the repository
- **When** its frontends are listed
- **Then** the React shell is the only one, and a guard asserts that nothing imports
  Streamlit
- **And** `make run` starts that shell

**Scenario:** what the acceptance tier proved is still proved

- **Given** the acceptance tests that drove the app through Streamlit's `AppTest`
- **When** the app is removed
- **Then** each behaviour they covered is asserted through the React shell's API instead, or
  named as deliberately dropped in the change's proposal and in `sprint-5-feedback.md`

**Scenario:** the docs describe what exists

- **Given** `README.md` and the tutorial
- **When** a reader follows the quick start
- **Then** every command they are given is one the repository has

It comes second so that no later story pays the two-frontend tax: stories 6, 7 and 10 all
put something new on the screen.

### 3. The turn is a workflow of named steps

As a developer of cora,\
I want a turn to run as a sequence of steps with one responsibility each,\
so that I can see where a turn is, control what each step may do, and test a step without
the whole loop.

**Scenario:** a turn walks its steps

- **Given** any question
- **When** the turn runs
- **Then** the trace names *screen*, *work* and *answer*, in that order — the three steps
  this story leaves the turn with
- **And** *screen* runs before the model is called at all
- **And** a step's failure is reported as that step's, with the conversation intact

**Scenario:** the model's freedom is bounded to one step

- **Given** a question that needs several rounds of tools
- **When** the turn runs
- **Then** the rounds happen inside the working step and nowhere else

The steps are named here and made subscribable in story 5. Naming them first means the event
list is a description of something that exists rather than a guess at one.

### 4. A plugin is handed cora, not a form to fill in

As someone writing a plugin,\
I want cora to hand me what it has and let me register what I have,\
so that what I can contribute is not limited to the fields someone else thought of.

**Scenario:** a plugin registers rather than declares

- **Given** a module defining `extend(cora)` instead of a `PLUGIN` record
- **When** it is loaded
- **Then** what it registered is what cora offers — its tools callable, its instructions in
  the brief, its rules screening input
- **And** the three shipped plugins are written this way, with no record left behind

**Scenario:** a plugin uses cora's own parts

- **Given** a plugin that wants to search, remember, or call the model itself
- **When** it is loaded
- **Then** the host it was handed gives it each of those, and the plugin's own log lines and
  configuration are named for it

**Scenario:** the sub-agent needs no core change

- **Given** a test plugin that registers a tool running its own bounded model loop
- **When** the model calls that tool
- **Then** it runs, its nested steps appear in the trace as children of the call, and
  nothing under `src/cora/` was changed to allow it

**Scenario:** a bad plugin is refused where it can be seen

- **Given** a module with no `extend`, one that raises while registering, or one registering
  a tool name that is cora's own
- **When** cora starts
- **Then** the refusal names that module and what is wrong with it

This story is the sprint's hinge, and it lands before the scope story because scope is a
property of a registration and there are no registrations until now.

### 5. A plugin can take part in the turn

As someone writing a plugin,\
I want to act at a named point in the turn rather than only before it starts,\
so that I can amend what the model is told, refuse a call before it runs, or wrap what comes
back — without asking for a new field.

**Scenario:** cora's own steps are subscribers

- **Given** the injection screen and the input rules cora ships
- **When** a turn runs
- **Then** they run as handlers on the same events a plugin subscribes to, and nothing in
  the core reaches them another way

**Scenario:** a handler amends what the model is told

- **Given** a plugin subscribing before the model is called
- **When** a turn runs in its scope
- **Then** what it returned is in the brief, and the trace attributes it to that plugin

**Scenario:** a handler refuses a call before it runs

- **Given** a plugin subscribing to the tool-call event and refusing one
- **When** the model asks for that tool
- **Then** the tool does not run, the model is told why, and the turn continues

**Scenario:** a system-wide rule cannot be scoped away

- **Given** a system-wide plugin loaded beside two scopes
- **When** an injection attempt arrives in any scope, or with none pinned
- **Then** it is refused before the model is called

**Scenario:** a scoped handler applies where it belongs

- **Given** a handler registered under a named scope
- **When** a turn runs in a different scope
- **Then** it does not run

**Scenario:** the medical filter moves to where it always applies

- **Given** the medical filter, today inside the fitness plugin
- **When** a medical question is asked in the travel scope, or with nothing pinned
- **Then** it is still refused, because the filter now ships system-wide

**Scenario:** a failing handler fails the right way

- **Given** a rule that raises and an observer that raises
- **When** a turn runs
- **Then** the rule's turn is refused, the observer's turn completes without it, and the
  trace names the plugin in both cases

### 6. A scope focuses the turn

As a person using cora for one field at a time,\
I want the scope to decide what cora is and what it can reach,\
so that a fitness question is answered by a coach, and a travel tool cannot be picked by
mistake.

**The travel plugin is not finished by this story.** It arrives here with its instructions
and its corpus, gains its live-service tool in story 9 and its effectful tool in story 10.
Story 6 ships enough of it for routing to have somewhere to route.

**Scenario:** the user pins a scope

- **Given** two scopes are loaded and I pin one
- **When** I ask anything
- **Then** only that scope's instructions and tools are in the prompt, beside the
  system-wide ones
- **And** the other scope's tools are not offered at all

**Scenario:** the pin survives the browser

- **Given** a thread pinned to a scope
- **When** I reload the page and reopen it
- **Then** it is still in that scope, because the pin is in the thread's own state

**Scenario:** nothing pinned, so cora routes

- **Given** two scopes are loaded and none is pinned
- **When** I ask a question that belongs to one of them
- **Then** the trace names the scope it routed to, and the turn runs in that scope

**Scenario:** it asks rather than guessing

- **Given** a question that fits both scopes or neither
- **When** the turn runs
- **Then** cora asks which scope was meant, and answers with the one I choose

**Scenario:** the routing step is wired correctly

- **Given** a scripted model that names a scope
- **When** the turn runs
- **Then** it runs in that scope, and the trace says so — asserted in the default tier,
  where no model is called

**Scenario:** routing is measured, not assumed

- **Given** a recorded set of questions with the scope each belongs to
- **When** the router is run over it against a real model, in the `llm` tier
- **Then** a report names how often it chose the right scope, and a drop below the recorded
  threshold fails that tier
- **And** the number is quoted in the change's `proposal.md` when it is first measured,
  because the tier is hand-run and costs money

### 7. A plugin comes from anywhere, and cora says what it loaded

As someone who wrote a plugin for my own field,\
I want to install it or drop it in a folder and have cora find it,\
so that using it does not mean forking cora.

**Scenario:** an installed distribution announces itself

- **Given** a plugin packaged as its own distribution, built outside this repository and
  installed into the environment
- **When** cora starts with nothing named in `CORA_PLUGINS`
- **Then** it is loaded, because it declared an entry point in the `cora.plugins` group
- **And** nothing under `src/cora/` names it

**Scenario:** a file is enough

- **Given** a single `.py` file in `~/.cora/plugins/` or `./.cora/plugins/`
- **When** cora starts
- **Then** it is loaded with no packaging at all, and the listing says where it came from

**Scenario:** cora says what is loaded

- **Given** several plugins from different sources
- **When** I ask cora what it has
- **Then** each one is listed with its source, its scope, its tools, its rules and the steps
  it subscribes to
- **And** the same listing is on the screen, not only in a terminal

**Scenario:** the contract has a version and says so

- **Given** a plugin declaring a contract version cora does not support
- **When** it is loaded
- **Then** the refusal says which version it wants and which cora offers
- **And** `docs/how-to/write-a-plugin.md` names what is public, what may move, and what a
  change to the public part obliges cora to do

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

### 10. cora acts, but only when I say so

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

**Scenario:** the gate is cora's, not the plugin's

- **Given** a plugin that marks a tool as having an effect
- **When** that tool is called
- **Then** the gate runs because cora subscribes to the tool-call event, and a plugin cannot
  unsubscribe it

**Scenario:** the result is mine to keep

- **Given** an approved effect that produces something — an itinerary, a training plan
- **When** it completes
- **Then** it exists as a file under the output location the app is configured with, outside
  cora's own stores, and `README.md` says where that is

### 11. What cora does with my data, and what a plugin costs in trust

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
  review of what a plugin's instructions tell the model ---

## Chores

Not stories — no failing test names them — but tracked, and each is a merge of its own.

- **The test suite, 20/80** — find the fifth of the suite carrying most of the protection,
  counted after story 2 takes the Streamlit tests with it. Extend only those, archive the
  rest under `tests/` and delete the archive after submission. Membership is decided by what
  would go undetected, not by count.
- **An architecture note for the React shell before story 6 touches it** — the scope pin and
  the plugin listing are both new things on the screen, and sprint 4 shipped that frontend
  with no such note and said so.
- **The showcase entry**, uploaded before the review and kept current, with its link in
  `README.md` (story 1's criterion).

## Evaluation-criteria coverage

| Criterion | Where |
|---|---|
| 1 · Outcome quality | *Purpose* above; stories 4, 5 and 7 make the plugin contract the product — a stranger can extend cora without forking it — stories 9 and 10 give the agent reach and consequence, story 6 gives it focus, story 1 says what it is for, and story 2 leaves one frontend to judge it by |
| 2 · Learning application | *Architecture decision* above — LangGraph as a named workflow with subscribable steps and an interrupt gate, Chroma for embeddings, OpenRouter behind the `ChatModel` port, an external API as a tool, and a plugin system whose model is named prior art rather than invented |
| 3 · Ethical considerations | Story 11, standing on sprint 4's injection screen and untrusted-data handling, on story 10's approval gate, and on story 5's rule that a system-wide screen cannot be scoped away |
| 4 · Presentation | The six points: the problem (story 1), the architecture (stories 3–7), the data (story 8), evaluation (story 6's routing report), the hardest problem (stories 4–5, the contract inversion), what is next (*Not in this sprint*) |
| 5 · Showcase submission | *Chores* — uploaded before the review, linked from `README.md` |

## Not in this sprint

Recorded with a reason. The items carried from sprint 4 are tracked in
`sprint-5-feedback.md`; the first four are this sprint's own deferrals, and this list is
their record.

- **A shipped sub-agent.** The contract no longer stands in the way — story 4 proves a
  plugin can run a bounded loop of its own with no core change — so this stops being an
  architecture deferral and becomes a plugin nobody has written yet. Research and booking
  are the two jobs that would earn one; story 9's tool is where the first would go.
- **A plugin depending on another plugin, overriding another's tool, or ordering itself
  against one.** Load order is the only precedence there is, and it is the order the sources
  were read in. All three are real needs of a mature harness and none is needed by three
  plugins; each is additive on `Host` when it is.
- **A sandbox, or any restriction on what a plugin's code may do.** A plugin runs with the
  user's full permissions, which is true of every harness of this kind, and story 11 says so
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
  two regexes. Story 11 says what it does not catch rather than implying it catches
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
- **A plugin registry or directory.** Entry points and a folder are discovery; a place to
  browse other people's plugins is a website, and there are no other people yet.
- **Multi-modal input, code generation, parameter-tuning studies** — cases 4, 5 and 7 are
  not the case this project answers.
- **Authentication, multi-tenancy, cost dashboards.** cora runs on the machine of the person
  whose documents it holds.
