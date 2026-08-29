## Why

None of `prepare → model ⇄ tools` is a place a turn can be *in*, and stories 5 and 6
need one.

## What Changes

- The turn becomes `screen → work → answer`, one responsibility each
- `screen` admits the question and opens the turn, before anything is written or called
- `work` holds the model's freedom: every round, and the budget that bounds them
- `answer` settles what the user reads, once, rather than a round setting it by being last
- The trace names each step as it is entered
- A failure carries the step it came out of, and the thread stays answerable
- The graph port takes the steps as a sequence, so story 6 extends it and not the adapter
- One modified capability, `conversation`; no `AgentState` key added or widened

## Impact

- `src/cora/ports/graph.py` — a named sequence and the loop's parts, not four slots
- `src/cora/engine/steps.py` — screening, answering and one wrapper that names a step
- `src/cora/domain/trace.py` — one new kind, the step a turn entered
- `src/cora/domain/errors.py` — a `CoreError` says which step it came out of
- `src/cora/adapters/langgraph_runner.py` — a graph built from the sequence, resized limit
- `src/cora/app/assembly.py` — wires the sequence
- `scripts/sequences.py` — the graph reader takes the walk from the composition root
- `docs/assets/round-map.svg`, `turn-map.svg` — redrawn
- `docs/happy-path.md`, `docs/how-to/watch-a-turn.md` — the steps a turn walks
- Left alone: the pause contract, `AgentState`, what the model is told, every other adapter
