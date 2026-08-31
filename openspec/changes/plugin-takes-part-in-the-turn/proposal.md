## Why

A plugin can only act before a turn starts, so amending the prompt or refusing one tool
call needs a new field on cora.

## What Changes

- A plugin subscribes to a named event: *screen*, *brief*, *tool_call* or *tool_result*
- A handler is handed frozen values and returns a refusal or an amendment, never state
- Amendments chain in load order, and the second handler sees what the first returned
- Cora's own input rules become system-wide handlers on *screen*, reached no other way
- **BREAKING** — `register_rule` and the `ValidationRule` port go, with no shim
- Every registration carries a scope, and `scope=None` is system-wide and unremovable
- The fitness plugin registers its medical filter system-wide, its rest under its scope
- The active scopes are a set on the turn's state, supplied by the caller until story 6
- A deployment names what a turn runs under in `CORA_SCOPES`, so the app still demos
- A refused tool call answers the model and the turn continues, spending no round
- A rule that raises refuses the turn; an amender or an observer that raises is dropped
- The trace names the plugin behind every amendment, refusal and failure
- Modified capability `plugins`; no new one, and `conversation`'s requirements stand

## Impact

- `src/cora/ports/host.py` — the event names, `register_handler`, a scope per registration
- `src/cora/ports/plugin.py` — `ValidationRule` removed, its moment now an event
- `src/cora/engine/events.py` — new: the event kinds, the table and the one dispatch
- `src/cora/engine/plugin_set.py`, `host.py` — the scope filter, and handlers by event
- `src/cora/engine/steps.py` — *screen*, the brief and the tool step dispatch their events
- `src/cora/engine/validation.py` — cora's rules become handlers it registers for itself
- `src/cora/domain/agent_state.py`, `trace.py` — the active scopes, and a handler's step
- `src/cora/app/config.py`, `engine/agent.py` — `CORA_SCOPES`, and the turn's default
- `src/cora/app/assembly.py` — seeds cora's own registrations before any plugin's
- `plugins/fitness/`, `plugins/security/` — rules rewritten as handlers, scopes declared
- `docs/how-to/write-a-plugin.md`, `docs/big-picture.md` — the contract gained an event
- `tests/guards/` — the architecture guard, and the diagram guard over the component map
- Left alone: the named steps, the pause contract, retrieval, memory, every adapter
