# Shortcuts for the commands whose paths are long enough to get retyped wrong. Everything
# here is a thin wrapper over `uv run` — the real definitions are in pyproject.toml, and
# `tests/guards/test_docs.py` checks that the path below still exists.

APP := frontends/streamlit/src/cora/frontends/streamlit/streamlit_app.py
REACT := cora.frontends.react.server

.PHONY: run run-env run-react run-env-react ui ui-build ui-test ui-test-browser docs docs-serve diagram

# Reads OPENROUTER_API_KEY from the environment.
run:
	uv run streamlit run $(APP)

# Reads it from .env instead, which is how the live tier is run too.
run-env:
	uv run --env-file .env streamlit run $(APP)

# The React shell. `ui` is the page in dev — Vite on 5173, proxying /api to the server
# below; `run-react` is the one process that serves both, and it builds first because the
# server only ever reads `ui/dist` — without this a source change is invisible on the page.
run-react: ui-build
	uv run python -m $(REACT)

run-env-react: ui-build
	uv run --env-file .env python -m $(REACT)

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

# The docs site — the two narrative pages and a reference generated from the source.
# `mkdocs.yml` configures it; --strict is what the integration tier runs, so a build that
# passes here is the one CI checks.
docs:
	$(QUIET_FORK) uv run mkdocs build --strict

# 8001, because the React shell already wants 8000: reading the docs beside the running
# app must not need one of them stopped. `tests/guards/test_docs_site.py` holds that.
docs-serve:
	$(QUIET_FORK) uv run mkdocs serve --dev-addr 127.0.0.1:8001

# The component map on `big-picture.md`: the script reads `cora.app.assembly` for what the
# boxes and the connectors are, and places them itself — the map has one fixed shape, so
# there is no layout to search for. The SVG is committed, and
# `tests/guards/test_component_map.py` fails when the committed file is not what this
# target writes, so a port added without a redraw is a red test.
diagram:
	uv run python scripts/gen_component_map.py
