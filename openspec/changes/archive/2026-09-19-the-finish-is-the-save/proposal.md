## Why

The trainer keeps a second copy of every workout in the browser, and the field's copy is the one cora reads.

## What Changes

- Finish is the one save: the workout goes to the field, and the page keeps no history of its own
- History, and a fresh workout's weights and reps, are read from the field's documents
- A save is named for its moment and then for the workout, as the sheet's tab names it
- A save cora did not take stays on the page with the finish offered again
- Import, Export and the clipboard go
- The coach dates a document named for its moment and its workout as one named for its moment
- Capability `plugins` — two requirements change, two are added, one goes

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `plugins`: the finish is the save, the History is the field's, the name carries the workout, a failed save stands

## Impact

- `plugins/fitness/src/cora/plugins/fitness/page/index.html` — history, import, export and clipboard go, the field is read instead
- `plugins/fitness/src/cora/plugins/fitness/workouts.py` — a dated name may carry the workout behind the time
- `plugins/fitness/tests/fitness/`, `frontends/react/ui/e2e/trainer.spec.ts` — the tests follow
- `openspec/changes/a-document-is-read-by-name` — the route this page reads by, merged first
- Left alone: cora's core, the upload route, the watch, the plan and the sheet
