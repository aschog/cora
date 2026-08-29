## Why

A plugin fills in a record cora defined, so what it may contribute is the set of fields
someone else thought of.

## What Changes

- A plugin defines `extend(cora)` and registers what it has; the `Plugin` record goes
- **BREAKING** — no shim: the two shipped plugins are rewritten to the new contract
- The host hands a plugin cora's own parts: search, memory, the model, a log, its settings
- Registrations are one list, so the listing, the collision check and the trace read once
- A registered tool may run a bounded loop of its own, offered read-only tools
- The steps that loop takes appear in the trace as children of the call that ran it
- A module with no `extend`, one that raises, or one taking a taken name is refused by name
- One new capability, `plugins`; no `AgentState` key added or widened

## Impact

- `src/cora/ports/plugin.py` — a host and a registration, in place of a record to fill in
- `src/cora/engine/plugin_registry.py`, `plugin_set.py` — `extend` is called, and what it
  registered is held
- `src/cora/domain/trace.py` — a step carries the steps taken inside it
- `src/cora/engine/tool_runtime.py` — a call collects what its tool did
- `src/cora/app/assembly.py` — builds the host and wires what was registered
- `plugins/security/`, `plugins/fitness/` — rewritten to `extend`, no record left behind
- `docs/how-to/write-a-plugin.md` — the page is about registering now
- `tests/guards/` — the architecture and packaging guards that name the contract
- Left alone: the turn's named steps, `AgentState`, the pause contract, every adapter
