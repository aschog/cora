## Why

The sprint-4 reviewer's first finding was that `README.md` does not convey the main idea:
the opening is one or two sentences and a reader does not learn what the solution is for.
The retrospective names the cause — the README was cut last — and its action is to write
the paragraph on day one, before the code. This change is that day.

## What Changes

- The one-sentence description becomes *cora is an agent you chat with, and everything it
  knows and can do arrives as a plugin.*
- New capability `front-door`, in `specs/front-door/spec.md`: what a reader is told before
  they read any code, and the guard that holds it there.

## Impact

- `README.md` — rewritten above the quick start.
- `docs/index.md`, `pyproject.toml`, `mkdocs.yml`, `CLAUDE.md` — the one sentence, held in
  step by `tests/guards/test_tagline.py`.
- `tests/guards/` — one new guard over the shape of the first screen.