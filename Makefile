# Shortcuts for the commands whose paths are long enough to get retyped wrong. Everything
# here is a thin wrapper over `uv run` — the real definitions are in pyproject.toml, and
# `tests/guards/test_docs.py` checks that the path below still exists.

APP := frontends/streamlit/src/cora/frontends/streamlit/streamlit_app.py
REACT := cora.frontends.react.server

.PHONY: run run-env run-react run-react-env ui ui-test

# Reads OPENROUTER_API_KEY from the environment.
run:
	uv run streamlit run $(APP)

# Reads it from .env instead, which is how the live tier is run too.
run-env:
	uv run --env-file .env streamlit run $(APP)

# The React shell. `ui` is the page in dev — Vite on 5173, proxying /api to the server
# below; `run-react` is the one process that serves both once `ui` has been built.
run-react:
	uv run python -m $(REACT)

run-react-env:
	uv run --env-file .env python -m $(REACT)

ui:
	cd frontends/react/ui && npm run dev

ui-test:
	cd frontends/react/ui && npm test
