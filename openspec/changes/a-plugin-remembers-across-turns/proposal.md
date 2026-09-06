## Why

A plugin keeps nothing between turns, so whatever it worked out is gone once the turn
ends.

## What Changes

- A plugin is handed a small store of its own, keyed by the conversation it runs in
- It reads and writes it inside a tool call, which is where the conversation is known
- Its keys are its own, so two plugins collide with each other no more than their settings do
- A value is text, because what a plugin keeps is the plugin's own to read back
- Deleting a conversation deletes what its plugins kept, as it deletes the turns
- A plugin running outside a turn keeps nothing, the way a step taken there is dropped
- New port `state`, bound where the conversation's own turns are already kept
- Capability `plugins` gains what a plugin may keep, and how long it lasts

## Impact

- `src/cora/ports/state.py` — new port: two verbs over what one conversation holds
- `src/cora/ports/host.py` — `Host.state`, added surface, so the contract version stands
- `src/cora/domain/agent_state.py` — the turn carries the conversation it belongs to
- `src/cora/engine/scoping.py` — the conversation is bound beside the fields, per call
- `src/cora/engine/steps.py`, `src/cora/engine/host.py` — bound at the call, namespaced per plugin
- `src/cora/engine/agent.py` — forgetting a conversation drops what its plugins kept
- `src/cora/adapters/sqlite_plugin_state.py` — new adapter, in the file the turns are in
- `src/cora/app/assembly.py`, `src/cora/app/config.py` — one more slot, wired like memory
- `README.md`, `docs/how-to/write-a-plugin.md` — that a plugin may keep something
- Left alone: what a plugin may register, and every plugin that keeps nothing
- Left alone: cora's memory, which is what cora knows about the user and not this
- Left alone: the gate, the trace, the citations and the shape of a turn
