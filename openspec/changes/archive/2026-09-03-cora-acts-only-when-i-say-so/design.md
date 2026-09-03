## Context

A tool already declares an effect and a turn already stops to ask, but nothing stands
between the two — see `proposal.md` for why that is now the gap.

## Goals / Non-Goals

**Goals** — a gate no call can go round, an approval bound to the call it answers, a
round whose approvals are all settled before any of it runs, and one configured place a
result lands in.

**Non-Goals** — editing an argument before approving, which the shape allows and no
story asks for. A sub-agent that proposes an effect, deferred with a reason. A sandbox
over what a plugin's own code may write. A second effecting scope.

## Decisions

**The gate is a node on the only path from the model to the tools.**

- The rounds become model → gate → tools, and the ask step leads into the gate as well.
- The router's vocabulary is unchanged: it still says "spend a round", and the wiring
  says the gate is what a round starts with.
- Unbypassable by construction rather than by discipline, which is what a guard can read.
- A round proposing no effect passes straight through, contributing nothing.
- Rejected: routing to the gate only when an effect is proposed — a path that skips it
  is a path a later change can be got at through.
- Rejected: a handler on the tool-call point — no handler may pause a turn, and one that
  could would be a plugin holding the gate.

**An approval is its own type, bound to one call.**

- What is proposed carries the call's id, the tool, what it says it does, and the
  arguments as written.
- What comes back carries that same call id and a yes or no, so two proposals in a round
  can never be confused.
- Rejected: a `Decision` with an approve option — a label is bound to nothing, and the
  second effect of a round has no way to say which one it settled.

**One stop per proposed effect, all of them inside the gate.**

- The gate proposes each in turn, so a round with two effects stops twice.
- A resumed node replays from its first line and the stops are matched in order, so what
  was already answered comes straight back.
- The node runs no tool, which is what makes replaying it free and what "settled ahead of
  execution" is made of.
- Rejected: one stop carrying every proposal — approving in a batch is one answer to two
  questions, and the story asks for each.

**A declined call is answered where it was proposed.**

- The gate writes the tool message the model reads, exactly as the ask step settles an ask.
- The tools then run what is left of the round, and need no notion of approval at all.
- Rejected: an approvals key in the state — a second record of what the transcript
  already holds, and every key there costs a migration to widen.

**Whatever answers the gate is read as a decline unless it is an approval of that call.**

- The answer arrives from outside the run, so it is checked rather than trusted.
- The default pause refuses, so a caller that cannot ask declines rather than acting.
- The same rule the ask step already applies to a label nobody was offered.

**A parked turn carries exactly one of a decision or a proposal.**

- One invariant on the shape, which is what `ToolResult` already does with its payload.
- Resuming carries a label or an approval, and each step checks what came back to it.
- Rejected: a second parked-turn shape — one thread stops one way at a time, and two
  would make the page ask twice which it was.

**Where a result goes is a port, and confinement lives in its adapter.**

- One write, answering with where the file landed, so the tool can say so in the turn.
- A plugin is handed that port and never a path, so no plugin writes the confinement
  check itself.
- A name resolving outside the root is refused, which is the claim story 12 will make.
- Rejected: a path in the plugin's own settings — a path is not a capability, and the
  check would be written once per plugin.

**The itinerary tool is plugin code over the port.**

- Registered under the travel scope, declaring its effect, writing through the host.
- The two-effect scenario is two calls of it, because a turn runs in one field and two
  scopes cannot both act in one.

**What moves at the edges.**

- Ports: `pause`, `graph` and `host` gain a shape each, and `output` is a new one.
- Guards: a new one reading the walk for a path to the tools that misses the gate.
- Diagrams: the component map, by the adapter and the port, and the round sequence, by
  the node the rounds now start with.
- The recursion limit grows by a superstep per round, and its measured test is re-sized.

## Risks / Trade-offs

- **A round of many effects stops many times** → the round is bounded by what the model
  proposed, and each stop is the approval the story asks for.
- **The user approves arguments a model wrote** → they are shown as written, and editing
  them is the deferral the shape leaves room for.
- **Confinement is a path check, not a sandbox** → true of the harness and said plainly,
  and story 12 is where it is said.
- **A gate on every round costs a superstep it does not use** → measured into the sizing,
  and cheaper than a path that skips the gate.
- **A frontend that cannot approve loses every effect** → it declines rather than acting,
  and the turn still answers.
