## Why

The sprint-4 reviewer's first finding was that `README.md` does not convey the main idea:
the opening is one or two sentences and a reader does not learn what the solution is for.
The retrospective names the cause — the README was cut last — and its action is to write
the paragraph on day one, before the code. This change is that day.

## What Changes

- The one-sentence description becomes *cora is an agent you chat with, and everything it
  knows and can do arrives as a plugin.*
- `README.md`'s first screen says what cora is for and how a turn works, above the quick
  start, and links the showcase entry near the top and the plugin how-to below it.
- The `front-door` capability is added: what the first screen says, and the rule that
  the sentence is written once and derived everywhere it is shown.

## Impact

- `README.md` — rewritten above the quick start.
- `docs/index.md`, `pyproject.toml`, `mkdocs.yml`, `CLAUDE.md` — the one sentence.
- `tests/guards/` — `test_tagline.py` and `test_docs_shape.py` removed; they held written
  pages to a shape, which is now against the rule in `CLAUDE.md`. `test_docs.py` stays: it
  checks whether what a page claims is true, not what the page says.
- No `src/` change, no dependency change, no runtime behaviour change.
