## Why

The deployment hands every turn its scopes, so cora cannot tell a fitness question from
a travel one.

## What Changes

- The turn gains two steps: *route* reads the question, *focus* settles the brief
- The brief moves out of *screen* into *focus*, which runs after the scopes are known
- An unpinned thread is routed every turn, and the trace names the scope it ran in
- A question fitting two scopes stops the turn to ask, through the pause already there
- A question fitting none runs in a named default scope, with only what is system-wide
- A thread carries a pin in its own checkpointed state, so a reload reopens in its scope
- A pin is set once and never changed — a second field is a second conversation
- Turns that ran before a pin read as they ran, and none is re-answered under it
- `CORA_SCOPES` now names the scopes a turn *may* run under, not the ones it does
- The travel plugin arrives with its instructions and its corpus, and nothing else yet
- The page offers the pin and reads back the one the thread already holds
- An `llm`-tier report measures the router: 16/16 first run, `gpt-4o-mini`, bar at 90%
- New capability `scopes`; modified `conversation` and `plugins`

## Impact

- `src/cora/engine/steps.py` — *route* and *focus* as steps, the brief moving to *focus*
- `src/cora/domain/agent_state.py` — the pin, beside the scopes a turn runs under
- `src/cora/domain/trace.py` — a step naming the scope a turn was routed into
- `src/cora/engine/agent.py` — the pin arrives with the question, and a changed one is refused
- `src/cora/app/assembly.py`, `src/cora/ports/host.py` — two more steps, and the default scope
- `plugins/travel/` — new: its instructions, its corpus and its scope
- `frontends/react/` — the pin control, the pin on a session, the routed scope on the trace
- `tests/acceptance/` — the recorded question set, the report and its threshold
- `tests/guards/` — the component map and the walkthrough's sequence diagrams
- `docs/happy-path.md`, `README.md`, `docs/tutorial/`, `docs/how-to/` — the steps, the pin, two fields
- Left alone: retrieval, memory, the stores, the approval gate, every adapter
