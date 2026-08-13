# Shortcuts for the commands whose paths are long enough to get retyped wrong. Everything
# here is a thin wrapper over `uv run` — the real definitions are in pyproject.toml, and
# `tests/test_docs.py` checks that the path below still exists.

APP := packages/frontends/streamlit/src/cora/frontends/streamlit/streamlit_app.py

.PHONY: run run-env diagram

# Reads OPENROUTER_API_KEY from the environment.
run:
	uv run streamlit run $(APP)

# Reads it from .env instead, which is how the live tier is run too.
run-env:
	uv run --env-file .env streamlit run $(APP)

# Rewrites every generated diagram page from the code — the workspace-wide one in docs/, and
# one beside every package that ships a diagram.py, plus the SVG graphviz draws from the DOT
# on that page. `tests` carries the fakes one scripted turn needs.
diagram:
	PYTHONPATH=tests:scripts uv run python scripts/diagrams.py
