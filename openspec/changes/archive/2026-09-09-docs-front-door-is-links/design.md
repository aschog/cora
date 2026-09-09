## Context

See proposal.md — Why. Ten pages, one fact each, and a guard that reads only whether a
path exists.

## Goals / Non-Goals

**Goals:**

- One home per fact, with the pages that repeated it linking instead.
- A front door a stranger reads in a screen.
- A test that fails when the docs name something the code does not have.

**Non-Goals:**

- Changing anything the pages describe.
- Guarding prose. A sentence about behaviour is held by a person reading it.

## Decisions

- The README states no sentence about what cora is, so the site states its own: a
  `site_description` in `mkdocs.yml`, and its own opening on `docs/index.md`. The build
  hook that read the README is deleted rather than pointed elsewhere.
- Duplication is measured, not judged: a sentence-similarity scan over every page, run
  before and after, is what said which pairs were real.
- Each page's cut was made from a fact inventory verified against the source first, and
  checked again after — because a page cut by a third loses a true sentence as easily as
  a false one.
- The drop-in folder is the only documented way to load a plugin. `CORA_PLUGINS` still
  works and is named nowhere in `docs/`.
- What a guard can hold is a name: a `CORA_*` variable, a `make` target, a path. That is
  where the test goes, and the rest stays a reading.

## Risks / Trade-offs

- Two pages include their commands from a third through MkDocs snippets, which render as
  raw text on GitHub — one source, at the cost of the file reading oddly there.
- A page that is one home for a fact is a page that must be found: the front door is now
  a list of links, and a reader who skips it loses the map.
