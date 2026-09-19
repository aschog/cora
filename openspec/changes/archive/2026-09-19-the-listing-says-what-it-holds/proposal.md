## Why

Shown a day's names alone, the coach called a workout a movement and said the log held no sets or reps.

## What Changes

- The names view puts a day's workouts first and marks an untitled save's lifts as such
- It closes with how many days and saves it lists, and that the numbers are in the details
- The brief tells the coach to add nothing about what the log does or does not hold
- Capability `plugins` — the listing's shape and the brief's rule change

## Impact

- `plugins/fitness/src/cora/plugins/fitness/workouts.py` — the names view's order, marker and closing line
- `plugins/fitness/src/cora/plugins/fitness/__init__.py` — one more sentence of the brief
- `plugins/fitness/tests/`, `tests/acceptance/` — the names view asserted
- Left alone: the detail view, the grammar, the trainer, and cora's search
