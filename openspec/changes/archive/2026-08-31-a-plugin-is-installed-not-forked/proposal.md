## Why

A plugin reaches cora only as a module path in `CORA_PLUGINS`, and nothing running says
what any of them registered.

## What Changes

- A `.py` file dropped in `./.cora/plugins/` is loaded, with no packaging at all
- Every plugin carries where it came from — a named module, or the file it was read from
- One listing names each plugin with its source, its scopes, its tools, its instructions
  and the events it subscribes to
- A system-wide registration is flagged in that listing, being a claim on every turn
- `make plugins` renders the listing in a terminal, over the app the deployment configured
- `/api/plugins` carries the same listing, and the header menu draws it instead of names
- A module declares `CONTRACT`, read before `extend` runs, and one cora does not offer is
  refused
- That refusal names the version the plugin asked for and the version cora offers
- `docs/how-to/write-a-plugin.md` names what is public and what may move
- A guard asserts that nothing under `src/cora/` names a plugin or a scope
- The travel plugin is read back against the contract, as a distribution and nothing more
- Modified capability `plugins`; no new one, and `frontend`'s one-screen rule stands

## Impact

- `src/cora/engine/plugin_registry.py` — the folder, the source per plugin, the contract check
- `src/cora/ports/host.py` — `Extension` carries its source, and the contract cora offers
- `src/cora/engine/plugin_set.py` — the listing, read off the registrations already held
- `src/cora/app/config.py` — where the plugins folder is, as a setting with a default
- `src/cora/app/assembly.py` — the folder's plugins loaded beside the named ones
- `src/cora/app/listing.py` — new: the listing rendered for a terminal, run as a module
- `Makefile` — `make plugins`, the one command that prints it
- `frontends/react/src/cora/frontends/react/api.py`, `payloads.py` — the listing over HTTP
- `frontends/react/ui/src/components/Header.tsx`, `api.ts` — the menu draws the listing
- `plugins/travel/` — read back against the contract, and unchanged if it holds
- `docs/how-to/write-a-plugin.md`, `README.md` — the folder, the version, what is public
- `tests/guards/test_architecture.py` — no shipped file names a plugin or a scope
- Left alone: the turn's steps, the events, routing and the pin, retrieval, every adapter
