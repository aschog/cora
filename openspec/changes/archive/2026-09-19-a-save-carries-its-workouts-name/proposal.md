## Why

A save says which exercises were done but not which workout it was, so the coach lists lifts where the reader wants the workout's name.

## What Changes

- The trainer takes the workout's name off the sheet it loads, from the CSV's own filename header
- A save opens with that name on its first line, above the exercises
- The log's grammar takes one line before the first heading as the session's name
- The listing names a day by its workouts, and by its exercises only where a save carries no name
- In detail, a day's line carries the workout's name beside the date
- Capability `plugins` — the save's text, the grammar and the listing change

## Impact

- `plugins/fitness/src/cora/plugins/fitness/page/index.html` — the name read, kept and written first
- `plugins/fitness/src/cora/plugins/fitness/workouts.py` — the title line, and the names view
- `plugins/fitness/tests/`, `tests/acceptance/`, `frontends/react/ui/e2e/trainer.spec.ts` — the name asserted
- `docs/what-ships-with-it.md` — what a day is named by
- Left alone: the hosts the page reaches, the store, and cora's search
