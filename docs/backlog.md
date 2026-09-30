# Backlog

This is the prioritized parking lot for planned work outside a sprint cycle.
When an item starts, open one OpenSpec change under `openspec/changes/`.

## Now

### 1. secure-network-surface

**Goal:** prevent accidental remote exposure.

Acceptance:
- Loopback startup remains the default and needs no token.
- Non-loopback startup refuses unless explicit network mode is enabled.
- Network mode requires an API token or equivalent protection.
- README or operator docs state what network mode exposes.

Suggested tests:
- Startup allows default loopback binding.
- Startup refuses public binding without explicit opt-in.
- API refuses missing or invalid credentials in network mode.

### 2. confirm-dangerous-tools

**Goal:** prevent silent model-driven mutation and command execution.

Acceptance:
- `bash` requires user approval before it runs.
- `write` has an explicit decision: approval-gated, or documented as field-local.
- Plugin tools marked `writes=True` are reviewed and consistently gated or renamed.
- Trace shows what was approved, declined, and skipped.

Suggested tests:
- A proposed shell command pauses for approval.
- A declined command does not run.
- An approved command runs exactly once.
- The chosen write behavior is covered by an acceptance test.

## Next

### 3. sqlite-schema-versioning

**Goal:** make persisted data upgradeable.

Acceptance:
- The shared SQLite file records an explicit schema version.
- Each store creates or migrates through one versioned path.
- Migrations are idempotent.
- An older fixture database opens and upgrades.

Suggested tests:
- A fresh database creates the current version.
- An old database upgrades to the current version.
- Running migrations twice leaves the database valid.
- Migration failure reports an actionable error.

### 4. quiet-ui-tests

**Goal:** keep UI test output signal-only.

Acceptance:
- Expected happy-dom iframe and script errors no longer print during passing tests.
- Passing tests do not emit `ECONNREFUSED` noise.
- Real failures still print useful context.

Suggested tests:
- Existing Vitest suite passes with clean stderr.
- Mocked iframe or script-loading behavior remains covered where needed.

## Later

### 5. lazy-document-stack

**Goal:** avoid loading embedding and vector infrastructure for a bare app.

Acceptance:
- Startup without document or indexing capability avoids constructing embeddings.
- The documents plugin still indexes and searches as before.
- Heavy dependencies are either justified in core or moved behind the plugin boundary.

Suggested tests:
- Assembly without document features does not construct embedder or retriever objects.
- Document upload and search still work with the documents plugin loaded.
- Packaging tests describe the chosen dependency boundary.

### 6. split-turn-steps

**Goal:** reduce the size and density of `src/cora/engine/steps.py`.

Acceptance:
- Behavior does not change.
- Public imports stay stable unless a change explicitly moves them.
- Architecture guards still pass.

Suggested tests:
- Existing engine tests pass unchanged before code movement.
- Import compatibility is guarded if public names move.

### 7. split-react-api

**Goal:** reduce the size and density of `frontends/react/src/cora/frontends/react/api.py`.

Acceptance:
- HTTP routes and payloads remain unchanged.
- Streaming behavior remains unchanged.
- Route registration stays easy to audit.

Suggested tests:
- Existing frontend API tests pass unchanged before code movement.
- Route table behavior is guarded if routes are moved.

### 8. split-plugin-host

**Goal:** reduce the size and density of `src/cora/engine/host.py`.

Acceptance:
- The plugin contract remains unchanged.
- Shipped plugins require no behavioral changes.
- Registration, state, store, files, and delegation logic have clearer seams.

Suggested tests:
- Existing host and plugin tests pass unchanged before code movement.
- Contract compatibility is guarded where public host names are moved.

## Operating rule

Open one OpenSpec change at a time, starting with `secure-network-surface`.
Do not batch these into one cleanup branch.
