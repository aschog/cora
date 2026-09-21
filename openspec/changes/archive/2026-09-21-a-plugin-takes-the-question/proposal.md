## Why

Every turn costs a model call, even one a plugin could answer from what it already holds.

## What Changes

- A sixth point in the turn: the question, its field settled, offered to a plugin to answer
- The first handler answering with text has answered the turn, and no round is spent on it
- What it wrote joins the conversation as the round the turn ended on, and is recorded like any answer
- The handlers at the answer still run on it, so a check on what the reader sees holds either way
- A handler answering with nothing, with anything but text, or by raising leaves the turn to the model
- What the plugin kept for the conversation is readable and writable inside that handler
- The point is scoped like every other: a field's plugin takes a question in its field and nowhere else
- Capability `plugins` — a handler may answer the question before the model reads it

## Impact

- `src/cora/ports/host.py`, `src/cora/engine/events.py` — the sixth event, and a kind that takes rather than refuses or amends
- `src/cora/engine/steps.py` — the step that offers the question at the marker the rounds fall inside, and the route out of it
- `src/cora/ports/graph.py`, `src/cora/adapters/langgraph_runner.py` — the loop's opening route, and the edge that skips the rounds
- `src/cora/app/assembly.py` — the wiring
- `scripts/sequences.py`, `docs/assets/round-map.svg`, `tests/guards/test_diagrams.py` — the fork drawn where the graph declares it
- `docs/happy-path.md`, `docs/how-to/write-a-plugin.md` — six points, and what a taking handler may do
- Left alone: the five points a plugin has today, the gate, the tools, and every plugin that ships
