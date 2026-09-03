## Why

A reader deciding whether to upload their documents or load someone else's plugin has
nowhere to read what either costs, and both costs are now real: seven stores, three
outbound hosts, and a plugin contract that runs arbitrary code.

## What Changes

- A privacy and ethics page says what leaves the machine, what is kept where, what the
  model is told, and where an answer can be wrong.
- It says what the injection screen catches and what it does not, and that no plugin can
  take the untrusted-data label off retrieved or fetched text.
- It says a loaded plugin is arbitrary code with the reader's own permissions, and that
  this is true of every harness of this kind.
- It separates what cora enforces whatever a plugin does — the approval gate, the
  untrusted label, the confined output directory, the reserved tool names — from what it
  does not: no sandbox, no network restriction, no review of a plugin's instructions.
- The `disclosure` capability is added: what cora is obliged to say about itself.
- One assertion holds the page's list of stores against the settings themselves; every
  other claim is held by a person reading it, as `CLAUDE.md` requires of prose.

## Impact

- `docs/privacy-and-ethics.md` — new, the page itself.
- `mkdocs.yml`, `docs/index.md`, `README.md` — the page in the nav and in the two lists
  of what the docs hold.
- `tests/guards/test_docs.py` — the page added to the pages whose locations are checked.
- Left alone: `src/`, the plugins, the frontends, every dependency, and every runtime
  behaviour — this change says what cora already does and changes none of it.
