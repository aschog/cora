## Why

A plugin has nowhere to put a file, so data it owns goes into the search index instead.

## What Changes

- A field keeps files of its own, in a directory per field, and none of them is embedded
- A plugin reads, writes, lists and drops the files of the field it runs in, by name
- A file is text, and what the text means is the plugin's business rather than cora's
- A name that would leave the directory is refused, and so is a file over the size cap
- The screen lists a field's files, reads one, writes one and deletes one, under its scope
- Capability `plugins` — a field keeps files as well as documents, beside the plugin's own store

## Impact

- `src/cora/ports/files.py` — the new port, a field's own directory read and written by name
- `src/cora/adapters/file_field_files.py` — a directory per field under the configured path
- `src/cora/engine/host.py`, `src/cora/ports/host.py` — `files` handed to a plugin beside `store`
- `src/cora/app/config.py`, `src/cora/app/assembly.py` — the path setting, and the wiring
- `frontends/react/src/cora/frontends/react/api.py` — four routes under `/api/scopes/{scope}/files`
- `tests/guards/test_architecture.py` — the port stays a Protocol the adapter satisfies
- `docs/data-storage.md`, `docs/how-to/write-a-plugin.md` — the layout, and what a plugin may keep
- Left alone: documents, the index, the plugin store, the rail, and every plugin that has one today
