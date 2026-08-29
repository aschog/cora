## Context

Four slots today, and any reshaping keeps LangGraph's per-node checkpointing, which
story 11's gate leans on.

## Goals / Non-Goals

**Goals** — three named steps, one responsibility and one trace entry each; the loop
inside *work* with per-round replay granularity intact; story 6 inserting *route* and
*focus* by extending a sequence rather than editing the wiring.

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

**`work` is a compiled inner graph, invoked from the outer node for the keys it appended.**

Measured against langgraph 1.2.10, not assumed:

- A resumed node replays from its first line, so nothing already run may sit ahead of it.
- A subgraph added *as a node* double-applies every `operator.add` key, so it was
  rejected.
- The parent's own accumulation returns in the subgraph's output and is added again.
- Returning `output[len(input):]` per key is exact instead, and well-defined because the
  keys are append-only.
- `interrupt` inside the inner graph travels out of the nested invoke.
- The parked decision is visible on the outer thread, and resuming does not re-run the
  node that ran.
- So the ask keeps working, and story 11's gate has its property.
- The outer node yields once, so the run is streamed with `subgraphs=True`.
- The inner supersteps then arrive as they happen, and the namespace is dropped.
- *work*'s marker is written inside the inner graph, not by the wrapper around it.
- The wrapper re-runs on resume; a checkpointed inner node does not.

**Each step's responsibility.**

- *screen* admits or refuses the question, then opens the turn: transcript, marks, brief.
- Refusing costs the thread nothing, as today, and story 6 takes brief-building out.
- *work* holds the rounds and the budget that bounds them.
- It is the story's one claim that needs a containing step to be true.
- *answer* reads the round that ended the turn and settles the answer once.
- `ModelStep` sets it today as a side effect of being last.
- Story 9's cited live sources then have somewhere to compose.

**The router stays the loop's.**

- It reads the state and names `DONE`, `TOOLS` or `ASK`.
- The only change is that `DONE` now leaves the inner graph rather than the turn.

## Risks / Trade-offs

- **`scripts/sequences.py` reads one `_graph` method by AST, and there are two now** →
  the reader follows the inner builder.
- **`round-map.svg` and `turn-map.svg` go stale, and no guard catches that** → someone
  has to remember the redraw.
- **The recursion limit was sized against a flat graph** → resize it against the outer
  three plus the inner rounds.
- **A limit that trips before the core's round budget** → a legitimate turn reads as a
  runaway one.
- **A delta by length holds only while the keys are append-only** → they are, and
  `AgentState` says so.
- **A key that ever needed replacing** → the wrapper would have to say how.
