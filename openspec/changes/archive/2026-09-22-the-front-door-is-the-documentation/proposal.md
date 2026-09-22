## Why

The documentation site is gone, and the front-door spec still requires it — that
`README.md` link rather than state, that the site describe itself, and that a guard hold
the names the pages claim.

## What Changes

- The docs site goes: `mkdocs.yml`, the fifteen written pages, `scripts/gen_reference.py`,
  and the five mkdocs dependencies with `pyyaml` behind them.
- `README.md` states the commands it used to link — install, load the plugins, run, gates
  — and gains a short section on what a plugin must export and where it is dropped.
- **BREAKING** for a reader's bookmarks: every `docs/*.md` page and every `make docs`
  command is gone. The README is the documentation.
- The front door's requirements invert: it carries the commands rather than linking them.
- The two requirements that described the site and its guard are removed, not replaced.

## Impact

- `openspec/specs/front-door/spec.md` — one requirement modified, one added, two removed
- `README.md` — the commands, and a plugin section
- `mkdocs.yml`, `scripts/gen_reference.py`, `docs/index.md` and the fourteen pages beside
  it, `docs/cora_mockup.html` — deleted
- `tests/guards/test_docs.py`, `tests/guards/test_docs_site.py`, `tests/guards/conftest.py`,
  `tests/acceptance/test_docs_site.py`, `tests/helpers/site_config.py` — deleted with what
  they held
- `pyproject.toml`, `uv.lock`, `Makefile` — the mkdocs dependencies and the two targets
- `openspec/config.yaml`, `docs/workflow.md` — repointed off the two deleted pages
- `docs/sprints/` — pruned to the four files `docs/workflow.md` names
- Leaves alone: every line of `src/`, the generated diagrams under `docs/assets/` and
  `make diagram`, and `docs/workflow.md` as the process it remains
