## Why

The fitness field coaches in prose and has nowhere to train, so what was actually
lifted never reaches the documents cora answers from.

## What Changes

- The fitness plugin brings its field a page: a trainer worked one exercise at a time
- The trainer carries its own plan of exercises, their clips, and a camera to film against
- Finishing a workout uploads it into the fitness field as a dated Markdown document
- What it writes is a session anyone can read — a heading per exercise and its sets
- cora answers about it from its own document search, citing the day it came from
- A save that fails says so and leaves the workout where the reader can copy it
- Nothing of cora's own leaves: no sheet to sync from, no token, no second server
- What the trainer does fetch — its thumbnails, its clips, its pose runtime — is named
- Capability `plugins` gains what the fitness field brings

## Impact

- `plugins/fitness/src/cora/plugins/fitness/page/` — the trainer, its only new files
- `plugins/fitness/src/cora/plugins/fitness/__init__.py` — one more registration
- `tests/guards/test_installs.py` — a plugin's files that are not Python ship in its wheel
- `Makefile` — the browser tier runs the shipped plugin rather than a copy of it
- `docs/what-ships-with-it.md` — what fitness is, now that it has a screen
- `docs/privacy-and-ethics.md` — the three hosts a reader's browser reaches for it
- `README.md` — the trainer, among what cora ships pointed at
- Left alone: the calculators and the medical screen, which the field already had
- Left alone: the core, which `a-plugin-brings-a-page` finished
- Not here: reading the log back as numbers, which is its own change
