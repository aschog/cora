## Why

A plugin can screen what reaches cora but never what leaves it, so there is nowhere to
redact an answer before the reader sees it.

## What Changes

- A fifth point in the turn: the answer, settled and not yet handed over
- A plugin subscribed there is given the answer and may hand back a different one
- Amendments chain in load order, so a redaction and a rewrite both apply
- A handler that breaks is dropped and the turn answers, as an amending handler already is
- It amends and never refuses, so a blocked answer is a sentence rather than a lost turn
- Citations are read off the answer that was amended, so a redacted claim drops its number
- The trace names the plugin that changed it, as it names every handler that acts
- Capability `plugins` gains what a plugin may do to the answer

## Impact

- `src/cora/ports/host.py` — `ANSWERING`, the fifth name a plugin may subscribe to
- `src/cora/engine/events.py` — one entry in `EVENTS`, which is what a new point costs
- `src/cora/engine/steps.py` — the answer step dispatches before it settles the answer
- `src/cora/app/assembly.py` — the answer step is handed its handlers, as the others are
- `README.md`, `docs/how-to/write-a-plugin.md` — the fifth point, and what it is for
- Left alone: the four points that exist, and every handler subscribed to them
- Left alone: the model's own prose on the trace, which this does not reach
- Left alone: the gate, the citations machinery and the shape of a turn
