## Context

A plugin's rule, instructions and tools are three moments hard-coded because there was
one of each, and only the first is a point in the turn a plugin can reach.

## Goals / Non-Goals

**Goals** — one mechanism for taking part in a turn, which cora's own screening goes
through too. A scope on every registration, so story 6 routes rather than reshapes. A
handler that stays a function: frozen values in, a decision out.

**Non-Goals** — routing, the pin, and how a real turn acquires a scope, all story 6. The
approval gate, which stands at the tool-call point but is a privileged step rather than a
handler, story 11. A plugin ordering itself against another, deferred with a reason. Any
event on the answer the user reads.

## Decisions

**An event is a name in the port and a kind in the engine.**

- `cora.ports.host` names the four events, because a plugin subscribes by name and that
  name is contract.
- The engine holds the table from name to kind, as `ports.graph` names the routes and
  `Router` decides between them.
- Two kinds, each a class: one that refuses, one that amends.
- A refusing kind carries the exception its refusal is raised as, so *screen* ends the
  turn and *tool_call* ends one call.
- A new event is an entry in the table; a new kind is a new class. Neither edits a switch.
- Rejected: a handler declaring its own role, which lets it subscribe a rule where an
  amendment belongs.

**Dispatch is one verb, and the kind decides what a return means.**

- One call — the event, the value, the active scopes — answers with the value to carry on
  with.
- On a refusing event a handler returns a refusal or nothing, and the refusal comes back
  as that event's exception.
- On an amending event a handler returns a new value or nothing, each handed what the last
  returned.
- An observer is an amending handler that returns nothing, so watching needs no third
  kind — and a method per kind at the call site would be the switch the table avoids.

**A refusal is returned, and raising is what going wrong means.**

- Answering with a refusal value keeps a refusal and a bug distinguishable at the seam.
- Raising on a refusing event refuses anyway: a broken rule must not admit an input.
- Raising on an amending event drops that handler alone: a lost amendment is not a lost
  turn.
- Only the kind of a raised exception is passed on, as a tool's already is — its message
  could carry what the handler held.

**`ValidationRule` goes, because two doors to one moment is what the story forbids.**

- Cora's own rules become system-wide handlers on *screen*, registered through the host
  every plugin uses.
- `register_rule`, the `ValidationRule` port and the rules list all go, with no shim.
- Cora registers under its own module name, seeded first — which is what "cora's screen
  first" means.

**Instructions stay a registration rather than becoming a brief handler.**

- They are a string, and every plugin wanting a persona would otherwise write a closure
  — and the brief's `## Fitness` headings are composed from the registration, which no
  handler can be trusted with.
- A plugin wanting instructions that differ per turn subscribes to *brief*, which is the
  capability the story asks for.

**Scope is one field, and applying is one filter.**

- `Registration` carries a scope, and the register calls take it, defaulting to
  system-wide.
- One filter — system-wide, or named among the active scopes — is read by handlers, tools
  and instructions alike.
- "Cannot be scoped away" falls out of that filter rather than being enforced anywhere.
- The active scopes are a checkpointed set on the turn's state, plural from the start so
  story 6 costs no migration, and supplied by the caller until it lands.

**A tool-call refusal reuses the path a refusing tool already has.**

- Raised as the exception a tool raises, which the runtime already turns into a result the
  model reads — so "the turn continues" needs no new path and no round.

**The trace gains one kind, found rather than listed.**

- One step naming the plugin, the event and what came of it, contributed by the step it
  ran in — and subclass discovery already carries a new kind through both stores.

## Risks / Trade-offs

- **The contract breaks for the second sprint running** → both plugins live here, and one
  moment with two doors is what scenario one forbids.
- **The turn's state gains a key every stored thread then carries** → taken now, and taken
  as a set, so story 6 adds no migration.
- **A *brief* amender can rewrite cora's own preamble** → unmitigated: safety lives on
  *screen*, and *screen* cannot be amended.
- **The medical filter is absent when the fitness plugin is not loaded** → it is that
  plugin's rule, registered where no scope can switch it off.
- **A handler runs on every turn, so a slow one is a slow turn** → it is code the
  deployment named, and the trace says which plugin.

## Migration Plan

None: a store written before this sprint is deleted and re-ingested, as the sprint says.
