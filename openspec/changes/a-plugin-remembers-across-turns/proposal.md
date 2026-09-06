## Why

A plugin keeps nothing between turns, so whatever it worked out is gone once the turn
ends.

## What Changes

- A plugin keeps text under a name of its own, and reads it back on a later turn
- What it keeps rides the turn's own state, so the checkpointer holds it like the rest
- Its keys are its own, so two plugins collide with each other no more than their settings do
- A value is text, because what a plugin keeps is the plugin's own to read back
- A tool's writes are collected while the call runs and merged after it, as a card's values are
- Deleting a conversation drops what its plugins kept, because the thread it rode goes
- A plugin running outside a tool call keeps nothing, the way a step taken there is dropped
- Capability `plugins` gains what a plugin may keep, and how long it lasts

## Impact

- `src/cora/domain/agent_state.py` — one key: what each plugin kept, by plugin name
- `src/cora/ports/host.py` — `Host.state`, added surface, so the contract version stands
- `src/cora/engine/keeping.py` — new: the snapshot a call reads and the writes it collects
- `src/cora/engine/steps.py` — the tool step binds it, and merges the writes as the gate merges `filled`
- `src/cora/engine/host.py` — the plugin's name namespaces every key it reads or writes
- `README.md`, `docs/how-to/write-a-plugin.md` — that a plugin may keep something
- Left alone: no new port and no adapter — the checkpointer already keeps a thread's state
- Left alone: `Agent.forget`, which drops the thread and takes what rode on it
- Left alone: cora's memory, which is what cora knows about the user and not this
- Left alone: the gate, the trace, the citations and the shape of a turn
