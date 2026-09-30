## Why

Binding cora beyond loopback currently exposes private data and model-driven commands without authentication.

## What Changes

- Extend `frontend` with explicit network opt-in and authentication across its HTTP surface.
- **BREAKING**: refuse non-loopback startup unless network mode and an API token are configured.
- Keep default loopback startup token-free and preserve authenticated browser access through native HTTP login.
- Defer authenticated watch support and document that existing watch requests will be refused.
- Document exposed capabilities, credential handling, and transport limits for operators.

## Impact

- `frontends/react/src/cora/frontends/react/` — validate network settings and guard requests before route dispatch.
- `frontends/react/tests/` — cover startup refusals, authenticated access, origin checks, and streaming behavior.
- `README.md` — explain network access, native browser login, transport precautions, and deferred watch compatibility.
- `docs/backlog.md`, `openspec/changes/secure-network-surface/` — move this story into its in-flight change.
- `src/cora/`, plugins, watch tooling, Makefile, Telegram, dependencies, and generated diagrams — remain unchanged.
