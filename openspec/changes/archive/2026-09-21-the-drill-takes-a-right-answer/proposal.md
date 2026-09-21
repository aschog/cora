## Why

A right answer costs a model round to judge and to put the next word, so a drill runs at the model's pace.

## What Changes

- The drill takes an answer that is the other side of the word on the table, and puts the next word itself
- No model is asked for a right answer: the word is recorded, the pass moves, and the next word is what the reader reads
- A right answer given after the model was asked while the word stayed on the table counts as missed: what it gave was a hint
- Everything else still reaches the model: a hint asked for, an answer that is not the word, the last word of a pass, a spaced session
- The field tells the model that right answers never reach it, and that the word on the table is the last one put
- Capability `plugins` — the drill takes a right answer, and the model judges only what is not one

## Impact

- `plugins/vocab/src/cora/plugins/vocab/drill.py` — the handler that takes an answer, and whether the model was asked since the word was put
- `plugins/vocab/src/cora/plugins/vocab/__init__.py` — the handler registered at the taking point, and the instructions
- `openspec/specs/plugins` — what a right answer costs
- Left alone: the pass, the schedule, the check on the answer, the lists, and how a word is put
