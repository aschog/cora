## Why

A field holding several lists drills all of them at once, and nothing asks which one the reader meant.

## What Changes

- A drill in a field holding more than one list is refused until the reader has chosen one
- The choice is put as a card: one option per list, and one for all of them together
- What was chosen lasts the conversation and is asked once, not once per word
- A field holding one list is drilled without asking, because there is nothing to choose
- Capability `plugins` — which of a field's lists a drill runs over

## Impact

- `plugins/vocab/src/cora/plugins/vocab/drill.py` — the chosen list, kept and read
- `plugins/vocab/src/cora/plugins/vocab/__init__.py` — the argument, and the instruction to ask first
- `plugins/vocab/src/cora/plugins/vocab/lists.py` — the names a refusal offers
- `openspec/specs/plugins` — a drill runs over the list the reader chose
- Left alone: the schedule, SM2, how a word is put, the lists themselves, and cora's own card
