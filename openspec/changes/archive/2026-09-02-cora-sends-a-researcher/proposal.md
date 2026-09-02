## Why

A broad question takes several lookups, and one pass answers it by picking whichever
lookup the model thought of first.

## What Changes

- The travel scope gains a researcher: a tool running a bounded loop that reports back
- A loop reaching its ceiling reports what it found, marked incomplete, rather than losing it
- A tool declares whether it changes anything outside cora, as a field on its registration
- A sub-agent is offered no tool that declares one, so it reads and cannot act
- The researcher's rounds are the deployment's to set, read from the plugin's own settings
- Modified capability `plugins`, whose delegation requirement this changes

## Impact

- `src/cora/ports/plugin.py`, `src/cora/ports/host.py` — a tool declares an effect, and the contract says so
- `src/cora/engine/host.py` — the ceiling reports instead of refusing, and effects are withheld from a loop
- `plugins/travel/` — new: the researcher, its brief, its rounds setting and the refusal for a bad one
- `tests/cora/engine/test_host.py` — a sub-agent is offered nothing that writes, stops the turn or has an effect
- `docs/how-to/write-a-plugin.md`, `README.md` — declaring an effect, and what a sub-agent may be handed
- `docs/sprints/5/spec.md` — story 10 leaves it, and its stale claim about the shell is corrected
- Left alone: the React shell, which already draws a nested step; citations, routing, the pin, memory
- Left alone: the approval gate an effect will pass through, which is story 11's
