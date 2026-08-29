## Context

Four slots today, and any reshaping keeps LangGraph's per-node checkpointing, which
story 11's gate leans on.

## Goals / Non-Goals

**Goals** — three named steps, one responsibility and one trace entry each; the rounds
bounded by *work*'s marker, with per-round replay granularity intact; story 6 inserting
*route* and *focus* by extending a sequence rather than editing the wiring.

**Non-Goals** — subscribers on a step (story 5); a nesting trace (story 4's shape — the
marker is flat here and becomes a parent there); any change to `AgentState`, to what the
model is told, or to the pause contract.

## Decisions

**The turn is a sequence the port is handed, not four named slots.**

- `GraphFor` takes the steps before the loop, the loop's parts, and the steps after.
- Story 6 then adds *route* and *focus* to the leading sequence, and the adapter learns
  nothing.
- The loop stays named apart: it alone has a router, and it alone may stop.
- Uniform entries would make the adapter switch on kind — the switch the north star
  forbids.

**One wrapper names a step and owns what a name buys.**

- It records the step's marker as that step's first contribution.
- It tags a `CoreError` on the way out with the step it came from.
- Three uses, one place, and story 5's subscribers attach here rather than per step.
- The user-facing sentence is untouched.
- The step is a field for the log, the trace and the error payload.

**The turn stays one flat graph, and *work* is a node of it.**

Measured against langgraph 1.2.10, not assumed:

- A nested graph was tried first, so that *work* would contain its own rounds.
- A node that raises contributes nothing, and the parent keeps only what one returned.
- A model that failed in round two therefore lost every round the turn had spent.
- The inner checkpoint also outlived the turn, and the next turn's invoke replayed it.
- The transcript then held the turn before it twice, on the happy path.
- Both properties rest on per-node checkpointing, which the flat graph keeps.
- So *work* is a step of its own, contributing its marker and nothing else.
- Every round falls between that marker and *answer*'s, which is the story's claim.
- A checkpointed node does not re-run on resume, so the marker is written once.
- `interrupt` and the parked decision are exactly as they are today.
- The loop keeps its own router, and `DONE` now leaves it for *answer*.

**Each step's responsibility.**

- *screen* admits or refuses the question, then opens the turn: transcript, marks, brief.
- Refusing costs the thread nothing, as today, and story 6 takes brief-building out.
- *work* holds the rounds and the budget that bounds them.
- It is the story's one claim that needs a step of its own to be true.
- *answer* reads the round that ended the turn and settles the answer once.
- `ModelStep` sets it today as a side effect of being last.
- Story 9's cited live sources then have somewhere to compose.

**The router stays the loop's.**

- It reads the state and names `DONE`, `TOOLS` or `ASK`.
- The only change is that `DONE` now leaves the loop for *answer*, not the turn.

## Risks / Trade-offs

- **`scripts/sequences.py` reads the runner's node statements, and a sequence is not
  literal there** → the reader takes the walk from the composition root, which is where
  the steps are named, and the loop's wiring from the runner as before.
- **`round-map.svg` and `turn-map.svg` go stale, and no guard catches that** → someone
  has to remember the redraw.
- **The recursion limit was sized against four slots** → resize it against the three
  named steps and the rounds between them.
- **A limit that trips before the core's round budget** → a legitimate turn reads as a
  runaway one.
- **Three steps where there was one, so a turn costs two more supersteps** → sized into
  the limit, which is why the round budget still trips first.
- **A marker node that contributes only a trace entry** → it is the cheapest way for a
  turn to say where it is, and story 5 hangs its subscribers there.
