## Why

Every save of a day is a document of one name, so the rail shows one entry for five workouts and nothing says which came first.

## What Changes

- The trainer names a save for its moment, `YYYY-MM-DD-HH-MM-SS.md`, the day first so it sorts and reads
- The listing still reads the day from the name, with or without a time behind it
- A day's saves list in the order of their time, whatever order they were uploaded in
- Capability `plugins` — the save's name and the listing's order change

## Impact

- `plugins/fitness/src/cora/plugins/fitness/page/index.html` — the name a save is posted under
- `plugins/fitness/src/cora/plugins/fitness/workouts.py` — the name's grammar, and the order within a day
- `plugins/fitness/tests/`, `tests/acceptance/`, `frontends/react/ui/e2e/trainer.spec.ts` — the name asserted
- `docs/what-ships-with-it.md` — named for the moment, not the day
- Left alone: the document store, which already keeps two uploads of one name apart
