## Why

The front door had grown into a manual: 348 lines of README that no test could hold
against the code, and most of it wrong somewhere.

## What Changes

- `README.md` becomes the hero image, what cora is for, and links — 32 lines.
- Its content moves to pages that own it, five of them new, each cut to what it states.
- The one sentence saying what cora is leaves the README, so the site states its own
  description and `scripts/site_description.py` goes.
- Every claim on every rewritten page is verified against the source; about thirty were
  false, including two safeguards stated softer than the code.
- **BREAKING** for a reader's bookmarks: the quick start, the plugin folder rules and
  the gates are pages of their own now.

## Impact

- `README.md` — the front door, 348 lines to 32
- `docs/what-it-does.md`, `docs/what-ships-with-it.md`, `docs/data-storage.md`,
  `docs/how-to/get-started.md`, `docs/how-to/load-plugins.md` — new, carrying what left
- `docs/how-to/write-a-plugin.md`, `docs/privacy-and-ethics.md`, `docs/happy-path.md`,
  `docs/tutorial/first-session.md`, `docs/how-to/run-the-react-shell.md` — cut and corrected
- `mkdocs.yml`, `docs/index.md` — the nav, and the description the README no longer holds
- `scripts/site_description.py` — deleted; nothing reads the README at build time now
- `tests/guards/test_docs.py` — the new pages, and a guard for what the docs name
- Leaves alone: every line of `src/`, the diagrams, and what the pages describe
