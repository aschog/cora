## Context

Story 5 gave every registration a scope and every turn a set of active ones, supplied by
the caller or the deployment; nothing reads a question to choose.

## Goals / Non-Goals

**Goals** — a scope settled inside the turn, by a pin or by reading the question. Two more
named steps, so the brief is built after the scope is known. A pin that belongs to the
conversation and cannot be changed. A number for how well the router chooses.

**Non-Goals** — a scope owning its documents, story 8. Travel's live-service tool, its
researcher and its effect gate, stories 9 to 11. Unpinning a conversation, which the story
forbids on purpose. Routing into two scopes at once: the state stays a set, and the router
names one. Splitting what a scope fuses, deferred with a reason in the sprint's spec.

## Decisions

**The walk gains *route* and *focus*, and the brief moves into *focus*.**

- `screen` keeps admitting the question and opening the turn on the thread.
- `route` settles the active scopes; `focus` states the brief under them.
- The brief leaves `screen` because it cannot be written before the scope is known.
- `ports.graph` needs no change: the walk is already handed over as a sequence.
- The graph adapter sizes its recursion limit from that sequence, so two steps cost no knob.

**Screening stays ahead of routing, and a scoped screen is the price.**

- Routing calls the model, so an injection must be refused before it.
- A handler registered under a *scope* therefore never screens a routed turn.
- Accepted: every screen cora ships is system-wide, which is where the story puts safety.
- Rejected: screening twice, once before routing and once after — two doors to one moment.

**The pin is its own checkpointed key, and it arrives with the question.**

- `scopes` stays what this turn runs under; `pin` is what the conversation holds.
- Only a graph run writes a checkpoint, so the pin travels in beside the question, as a
  request `route` promotes — a seeded key is written before the screen runs, and a
  refused question must fix nothing.
- The first turn carrying a pin fixes it, and a later turn naming a different one is refused.
- The refusal is a core error naming the scope already held, so the page can say it.
- Rejected: the pin in the conversation store — the sprint's shapes put it in the turn's state.
- Rejected: a write path into the checkpointer outside a turn — a second door to one state.

**Routing reads the question with the model; *focus* is what asks the reader.**

- `route` holds the model and the scopes the deployment offers, and names one of them.
- Its answer is a set, as the shape requires, holding one member today.
- A two-field reading settles nothing and leaves the fields for `focus` to put to the reader.
- Split because a stopped step replays from its first line: a question read again can be
  read differently, and would then answer in a field the reader did not choose.
- So the reading commits a superstep before the stop, and the resumed step only reads state.
- `focus` calls `Pause` from inside itself, because the stop comes before the loop — and
  `ask_user`, the round's own tool, is untouched.
- Rejected: a fourth named step between the two, which buys the same separation and costs
  the walk a name nobody asked for.
- Routing that fails answers in the default scope: a broken reading leaves a turn less
  focused, never unanswered, and the trace says which happened.
- Rejected: routing as a tool the model calls in *work* — the brief would already be written.

**The default scope is a name, not an empty set.**

- A turn belonging to no scope runs under it, and the trace can then say which scope ran.
- Story 8 gives it a documents directory like any other's, which an empty set could not have.
- No shipped plugin registers under it: it is what a bare cora is.

**`CORA_SCOPES` becomes the scopes a turn may run under.**

- Routing chooses among them, so a deployment naming one leaves nothing to choose.
- That is how a single-field deployment stays single-field without pinning every thread.
- A caller naming scopes for one turn still wins, which is what the tests drive through.

**The trace gains one kind, naming the scope and how it was settled.**

- Pinned, routed, asked or default — one step, so a turn can be read back to its focus.
- Subclass discovery already carries a new kind through the checkpointer and the store.

**Travel ships instructions and a corpus, and no tool.**

- Routing needs a second field, not a second set of things to call.
- Its documents go into the one index, because a scope owns its files only in story 8.

**A pin naming a field nobody loaded is refused at the door.**

- The engine takes any name; what is on offer is the deployment's, and the API knows it.
- Refused there because a pin cannot be undone, so a wrong one would outlive every turn.
- The pin *conflict* is the engine's rule and arrives as a screening refusal does, on the
  stream.

**The page pins and reads the pin back off the session.**

- The control is a one-way door and says so before it is used.
- The session's own state answers what it is pinned to, so a reload draws the pin.

**The router is measured in the `llm` tier, against a recorded set.**

- Questions asked alone and as follow-ups, because an unpinned thread routes every turn.
- The share and the threshold live beside the set; the tier is hand-run and costs money.

## Risks / Trade-offs

- **An unpinned turn costs an extra model call** → a pin or a single-scope deployment avoids it.
- **A turn admitted and then failed still pins the thread** → the question was accepted, so
  the conversation is in that field; the page reads the pin back rather than assuming.
- **A mis-route answers in the wrong persona, quietly** → the trace names the scope, and the
  `llm` tier measures how often it is right.
- **Retrieval is not scoped until story 8** → a fitness turn can still cite a travel passage.
- **A pin cannot be undone** → the story's own trade-off: a thread's scope stays trustworthy.
- **The pin rides on the ask, so a client must resend it** → it reads back off the session.

## Migration Plan

None: a store written before this sprint is deleted and re-ingested, as the sprint says.
