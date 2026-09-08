## Why

Three database files hold what one can, and each is a path a deployment sets on its own.

## What Changes

- `CORA_DB_PATH` names the one file every store opens, defaulting to `.cora/cora.sqlite`.
- The index, the facts, the recorded turns and the checkpoints share it, each on its own
  connection.
- **BREAKING** `CORA_MEMORY_PATH` and `CORA_CONVERSATIONS_PATH` are gone.
- **BREAKING** the stores are cleared again, and nothing is carried over — the tables
  cora owns are renamed with it, so an old file's rows are read by nothing.
- A blank `CORA_DB_PATH` still falls back to the default rather than opening a database
  that dies with the process.

## Impact

- `src/cora/app/config.py` — one path constant where there were three
- `src/cora/app/assembly.py` — four stores opened at the same file
- `tests/cora/app/test_config.py` — the paths it asserts, and the variables it names
- `tests/cora/app/test_assembly.py`, `tests/helpers/live.py`,
  `frontends/react/tests/test_live_plugins.py` — the helpers that hand each store a path
- `tests/cora/app/test_plugin_settings.py` — the cora variable it holds out of a plugin's
  reach
- `docs/privacy-and-ethics.md` — three rows of the store table become one, which its
  guard already demands
- `README.md` — where cora keeps what it keeps
- Leaves alone: every port, the engine, the documents on disk, and what deleting a
  conversation or forgetting a fact does
