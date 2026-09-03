## Why

Every tool cora owns only reads, so the best a well-planned turn ever produced was a
better answer.

## What Changes

- A call to a tool that declares an effect stops the turn, saying what it will do
- The gate is a core step, standing on the only path from the model to its tools
- An approval is its own checkpointed type, bound to the one call it answers
- Every approval a round needs is settled before the round runs, so no effect runs twice
- A declined call never runs, and the turn says what it did not do
- A plugin is handed somewhere to put a result, confined to the directory configured
- The travel scope gains a tool that saves an itinerary as a file the user keeps
- The page draws the proposal and its arguments, with an approve and a decline
- New capability `effects`, which nothing before this change describes

## Impact

- `src/cora/domain/approval.py` — new: what is proposed, and the yes or no bound to it
- `src/cora/domain/decision.py` — `Pending` carries a decision or a proposal, exactly one
- `src/cora/ports/pause.py` — approving travels in, as asking already does
- `src/cora/ports/graph.py` — the loop gains a gate, and resuming carries an approval
- `src/cora/ports/output.py` — new: where a result is written, and what a name may not be
- `src/cora/adapters/file_output.py` — new: that port over a directory of files
- `src/cora/ports/host.py`, `src/cora/engine/host.py` — a plugin is handed the output location
- `src/cora/engine/steps.py` — new: the gate step, and what a declined call answers with
- `src/cora/adapters/langgraph_runner.py` — the gate node, its interrupt and the resized limit
- `src/cora/app/assembly.py`, `src/cora/app/config.py` — the gate is wired, `CORA_OUTPUT_PATH` read
- `plugins/travel/` — the itinerary tool, under the travel scope and no other
- `frontends/react/` — the approval card, the widened pending payload, the endpoint answering it
- `tests/guards/` — the gate is unbypassable, and the drawn maps match the walk
- `docs/sprints/5/spec.md` — story 11 leaves it for this change
- `README.md`, `docs/how-to/write-a-plugin.md`, `docs/big-picture.md` — the gate and the output location
- Left alone: routing, the pin, citations, memory, and what a sub-agent may be handed
- Left alone: editing an argument before approving, which the shape allows and no story asks for
