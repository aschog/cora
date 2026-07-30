# File logging on the debug seam

`enable_debug_logs` only writes to stderr, so a run leaves no trail once the terminal
scrolls. When `CORA_DEBUG` is on, also write the `cora` DEBUG stream to a file.

## Acceptance criteria

- `CORA_DEBUG=1` → the stderr handler stays; a `FileHandler` also writes to
  `.cora/logs/cora.log` (already gitignored), creating `.cora/logs/` first.
- File lines carry a timestamp + level (`%(asctime)s %(levelname)s %(name)s %(message)s`);
  the console keeps its terse `%(name)s %(message)s`.
- Off → early return, no file and no directory.
- Idempotent: re-running `build()` never stacks a second file handler or reopens the file.

## Design

- One file changes: `cora.app.log_config`. No new Config field, env var, or call site —
  `build()` keeps calling `enable_debug_logs(config.debug)`.
- Constants `LOG_FILE = ".cora/logs/cora.log"` and `FILE_HANDLER_NAME = "cora-debug-file"`
  beside the existing ones; guard the file handler by name like the stream handler.
- `enable_debug_logs` gains an optional `log_file` param (defaults to `LOG_FILE`) so tests
  point it under `tmp_path`. Test seam only — not an env var.

## TDD checklist

- [ ] enabled + `log.debug(...)` → file exists under a freshly-created dir, holds the
      message with a level and timestamp.
- [ ] disabled → no file, no directory, no file handler attached.
- [ ] two enabled calls → exactly one file handler (not reopened).
- [ ] enabled → stderr handler still attached alongside the file handler.
- [ ] `build(config, debug=True)` → both handler names on the `cora` logger; update the
      existing debug-seam build test to expect both.

## Fallout

`.cora/` is gitignored, so the build test writing the log needs no cleanup. Rotation and
a path override are out of scope.
