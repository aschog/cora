## Why

Cora's brief tells the model to spot a fact its notes hold at two or more values and ask
which was meant, and across three models it reliably did not.

## What Changes

- Cora reads its own notes and names, in the brief, every subject they hold at more than
  one value, so the model is told the conflict rather than asked to find it
- The rule above keeps the half that needs a reader: whether this answer turns on it
- Modifies `memory`: what cora states about the facts it holds, beyond listing them
- A subject is the words a note opens with before its first figure, so numeric
  disagreements are found and prose contradictions are still the model's to notice

## Impact

- `src/cora/engine/steps.py` — `_remembered` gains a section, `_conflicts` and
  `_subject_and_value` are new, `HELD_AT_SEVERAL` and its notice are new constants
- `tests/cora/engine/test_steps.py` — two tests, one per direction of the report
- `tests/acceptance/test_llm_acceptance.py` — the live ask test records what the change
  measured, and what it did not close
- `openspec/specs/memory/spec.md` — one requirement added
- The memory port, the `remember` tool, the store and the rail are untouched: what a
  fact is and how one is kept do not change
