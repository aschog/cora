## Why

The coach turns the tool's numbers into a table of its own and translates the names, so the reader gets more than asked and not as logged.

## What Changes

- `list_workouts` answers in text ready to show, not in numbers for the model to lay out
- Unasked for detail, a session is its day and the exercises worked, named as the log spells them
- Asked for detail, each movement carries its load, sets, reps, volume and whether it rose
- The brief tells the coach to pass that text on as it is, and to ask for detail only when the reader does
- Capability `plugins` — the listing's shape and the brief's rule change

## Impact

- `plugins/fitness/src/cora/plugins/fitness/workouts.py` — the two renderings replace the JSON
- `plugins/fitness/src/cora/plugins/fitness/__init__.py` — a third parameter, and the brief's line
- `plugins/fitness/tests/`, `tests/acceptance/test_fitness_log.py` — assert on text
- `docs/what-ships-with-it.md` — what the coach shows by default
- Left alone: the grammar, the filters, the trainer, and cora's search
