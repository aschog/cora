## Why

The coach finds a workout by its wording, so asked for every training it answers with the one that ranked.

## What Changes

- The fitness field offers `list_workouts`: every session the trainer logged, dated, with its movements
- Each movement is read back as numbers: load, sets, reps, volume, and whether it rose on the last time
- The list narrows to one exercise, or to sessions since a day, when the coach asks
- Two saves on one day are one session, and a document not named for a day is not one
- A dated document the grammar cannot read is left out, and the trace says which
- The coach is told to list for what was trained and to search for what a guide says
- Capability `plugins` gains what the fitness field lists

## Impact

- `plugins/fitness/src/cora/plugins/fitness/` — the log's grammar and the tool, in one new module
- `plugins/fitness/src/cora/plugins/fitness/__init__.py` — a fourth tool, and one more line of the brief
- `plugins/fitness/tests/` — the tool count, and a suite of the grammar's own
- `docs/what-ships-with-it.md` — what the coach can now say about the log
- After `a-plugin-reads-what-its-field-holds`, which hands the plugin the field it lists
- Left alone: the trainer page and how it names a save, the watch, and cora's search
