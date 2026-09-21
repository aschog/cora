## Why

A plugin's answer handler cannot read what its own tools kept, so it cannot check the answer against them.

## What Changes

- What a plugin kept for the conversation is readable, and writable, while its answer handler runs
- Bound the way a tool call already is, so one rule covers everywhere a plugin's code runs in a turn
- Capability `plugins` — where in a turn a plugin reads what it kept

## Impact

- `src/cora/engine/steps.py` — the answering step binds what was kept around its dispatch, and hands it back
- `tests/cora/engine/test_steps.py` — the step's state carries `kept`
- `openspec/specs/plugins` — a handler reads what a tool kept
- Left alone: the other four events, the tool round, the store, and every plugin
