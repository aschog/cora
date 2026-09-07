## Why

Installing a drop-in plugin today takes a restart, and a multi-module one cannot be
dropped at all without flattening it into one file.

## What Changes

- The plugins folder accepts a package directory — a folder with `__init__.py` — as
  one plugin.
- A dropped package is imported under cora's own namespace, its relative imports
  working as written.
- The folder name is the plugin's name, checked exactly as a file's stem is.
- A package that fails to import is refused by its folder name, like a file is.
- The folder is live: a drop installs, a delete removes, an edit reloads — no
  restart, a page reload shows it.
- A drop that cannot load refuses that reload readably and leaves the running set
  serving.
- Dependencies are not installed: an import the environment lacks is a refusal, not
  a feature.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `plugins`: the folder-drop requirement gains package directories beside single
  files, and the folder becomes live — the running set follows it, full sync.

## Impact

- `src/cora/engine/plugin_registry.py` — the folder scan and the file loader learn
  packages.
- `src/cora/app/assembly.py` — the composition rebuilds on folder change, over
  adapters that live on.
- `frontends/react/src/cora/frontends/react/api.py`, `server.py` — the API reads
  the current assembly instead of one fixed at boot.
- `openspec/specs/plugins/spec.md` — requirements gain package and live-folder
  scenarios, via this change's delta.
- `README.md`, `docs/how-to/write-a-plugin.md` — the drop-in section says folders,
  and says no restart.
- Named-module loading, `CORA_PLUGINS`, the contract check and the listing shape
  are left alone.
