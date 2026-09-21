## Why

Every session opens with the same three questions, and answers spacing nobody asked for.

## What Changes

- The left column of a list is German, and a drill puts it unless the reader says otherwise
- The field speaks German, because the reader it is drilling is reading in German
- Spaced repetition is off unless the reader turns it on, and writes nothing while it is off
- With it off, a session is one shuffled pass over the chosen list, each word once
- A word missed comes round again in the pass, and a word right does not
- A finished pass says so, and going again reshuffles the same list
- Every one of these lasts the conversation and no longer
- Capability `plugins` — how the vocab field opens a session, and what orders it

## Impact

- `plugins/vocab/src/cora/plugins/vocab/sweep.py` — one shuffled pass, kept for the conversation
- `plugins/vocab/src/cora/plugins/vocab/drill.py` — the pass beside the schedule, and which is running
- `plugins/vocab/src/cora/plugins/vocab/__init__.py` — the defaults, in the field's own instructions
- `openspec/specs/plugins` — what the field does before it is told anything
- Left alone: SM2 itself, the lists, the card that chooses one, and every other field
