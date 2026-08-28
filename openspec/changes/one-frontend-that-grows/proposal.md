## Why

cora ships two screens and this sprint puts four new things on one of them — the scope
pin, the plugin listing, the nested trace, the approval gate — so the second screen goes
now, before the first of them is built rather than after the last.

The story and its criteria: `specs/frontend/spec.md`.

## What Changes

- The Streamlit app, its tests and its workspace member are deleted
- What it proved is asserted through the React shell's API first, or named as dropped
- `make run` starts the React shell, and no second run target remains
- The quick start, the tutorial and the how-tos describe one screen
- A new capability, `frontend` — what cora is used through
- Two guards: one frontend in the workspace, and nothing imports Streamlit
- Dropped with it: every assertion about a Streamlit widget — a session-state key a
  click wrote, the tab list, the column weights — each describing one frontend's
  mechanics rather than a behaviour cora has. `design.md` maps the rest

## Impact

- `frontends/streamlit/` and `.streamlit/` — deleted, with the workspace member
- `tests/acceptance/` — four AppTest files and `tests/helpers/apptest.py` deleted
- `tests/acceptance/test_llm_acceptance.py` — driven through the shell's API instead
- `tests/guards/` — Streamlit drops out of five guards, and the import bar widens to the tree
- `Makefile` — `run` and `run-env` become the React shell, the rest of the run targets go
- `README.md` and `docs/tutorial/first-session.md` — the quick start points at that shell
- `docs/how-to/run-the-react-shell.md` — keeps its path, narrows to the development loop
- `docs/how-to/watch-a-turn.md` and `write-a-plugin.md` — one screen, not two
- `pyproject.toml`, `uv.lock`, `docs/assets/component-map.svg` — the member and the drawing
- `docs/sprints/5/sprint-5-feedback.md` — carries the dropped assertions, as the story asks
- No `src/` change beyond the deletion, and no change to what a turn does
