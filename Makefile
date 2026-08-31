# Shortcuts for the commands whose paths are long enough to get retyped wrong. Everything
# here is a thin wrapper over `uv run` — the real definitions are in pyproject.toml.

REACT := cora.frontends.react.server

.PHONY: run run-env plugins plugins-env ui ui-build ui-test ui-test-browser docs docs-serve diagram

# cora, as one process serving the page and the API on 127.0.0.1:8000. It builds first
# because the server only ever reads `ui/dist` — without that a source change is
# invisible on the page. Reads OPENROUTER_API_KEY from the environment.
run: ui-build
	uv run python -m $(REACT)

# Reads it from .env instead, which is how the live tier is run too.
run-env: ui-build
	uv run --env-file .env python -m $(REACT)

# What this deployment loaded, and what each plugin registered. It assembles the app the
# environment describes rather than reading the manifests, so what prints is what runs.
plugins:
	uv run python -m cora.app.listing

# The same, reading its environment from .env — as `run-env` is to `run`.
plugins-env:
	uv run --env-file .env python -m cora.app.listing

# The page on its own, for working on it: Vite on 5173, proxying /api to `make run`.
ui:
	cd frontends/react/ui && npm run dev

ui-build:
	cd frontends/react/ui && npm run build

ui-test:
	cd frontends/react/ui && npm test

ui-test-browser:
	cd frontends/react/ui && npm run test:browser

# MkDocs has forked: its owner is publishing a v2 that drops the plugin system, and
# `properdocs` is a continuation of 1.x that arrives here transitively. Both sides warn on
# every build, in opposite directions, and each reads its own variable. We stay on
# mkdocs 1.6.1, pinned by uv.lock, and say so once here instead of in every log.
QUIET_FORK := NO_MKDOCS_2_WARNING=true DISABLE_MKDOCS_2_WARNING=true

# The docs site — the written pages and a reference generated from the source.
# `mkdocs.yml` configures it; --strict is what the integration tier runs, so a build that
# passes here is the one CI checks.
docs:
	$(QUIET_FORK) uv run mkdocs build --strict

# 8001, because the React shell already wants 8000: reading the docs beside the running
# app must not need one of them stopped. `tests/guards/test_docs_site.py` holds that.
docs-serve:
	$(QUIET_FORK) uv run mkdocs serve --dev-addr 127.0.0.1:8001

# Every drawing in the docs. The component map reads `cora.app.assembly` for what the
# boxes and the connectors are and places them itself — that map has one fixed shape, so
# there is no layout to search for. The domain map is read out of the classes by pyreverse
# and laid out by graphviz, which this target needs installed. The session maps read one
# method each, and the graph off the nodes the runner declares, and space themselves to
# what is said on them. Every SVG is committed, and the guards beside them fail when a
# committed file is behind the source, so a port, a class or a call added without a redraw
# is a red test.
diagram:
	uv run python scripts/gen_component_map.py
	uv run python scripts/gen_domain_map.py
	uv run python scripts/gen_session_maps.py
