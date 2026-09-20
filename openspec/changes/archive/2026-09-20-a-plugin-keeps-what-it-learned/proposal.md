## Why

A plugin has nowhere to keep anything: what it keeps for a conversation goes with the
conversation, and cora's memory is about the user rather than about the plugin's work.

## What Changes

- A plugin is handed a store of its own, read and written by name, that outlives a turn
- What it keeps is namespaced under the plugin, so two plugins choosing one name differ
- It is text, as everything a plugin keeps is, and a name dropped takes its value with it
- It survives the conversation, the process and a restart, because it is in cora's own file
- A deployment without a store hands the plugin none, and the plugin says so rather than failing
- It is not memory: nothing kept here is about the user, shown in a rail, or put in a brief
- Capability `plugins` gains the store a plugin is handed

## Impact

- `src/cora/ports/store.py` — the port, beside the conversation-long one it is not
- `src/cora/adapters/sqlite_plugin_store.py` — a namespace of the store cora already keeps
- `src/cora/engine/host.py` — a plugin reaches its own, under its own name
- `src/cora/app/assembly.py` — built where the deployment has a file to keep it in
- `docs/how-to/write-a-plugin.md`, `docs/data-storage.md` — what a plugin may keep, and where
- Left alone: `State`, which is the conversation's and stays that way
- Left alone: `Memory`, which is what cora knows about the user
