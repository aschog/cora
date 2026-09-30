## Why

Binding cora beyond loopback currently exposes private data and model-driven commands without authentication.

## What Changes

- Extend `frontend` with explicit network opt-in and authentication across its HTTP surface.
- **BREAKING**: refuse non-loopback startup unless network mode and an API token are configured.
- Keep default loopback startup token-free and preserve authenticated browser access through native HTTP login.
- Give the watch a separate credential limited to writing one field's notice.
- **BREAKING**: require watch credentials when building its extension and starting its network server.
- Document exposed capabilities, credential handling, and transport limits for operators.

## Impact

- `frontends/react/src/cora/frontends/react/` — validate network settings and guard requests before route dispatch.
- `frontends/react/tests/` — cover startup refusals, authenticated access, and notice-only credentials.
- `Makefile`, `plugins/fitness/watch/`, `tests/guards/test_watch_build.py` — carry a scoped watch credential without printing secrets.
- `README.md` — explain network access, native browser login, watch setup, and transport precautions.
- `docs/backlog.md`, `openspec/changes/secure-network-surface/` — move this story into its in-flight change.
- `src/cora/`, other plugins, Telegram, dependencies, and generated diagrams — remain unchanged.
