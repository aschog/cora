## Why

A card of one box stops the conversation to collect what a sentence could have asked for.

## What Changes

- A card asking for exactly one writable value is refused before the turn parks.
- The model is told to ask for that value in its answer, and the reader replies in prose.
- Covers cora's own `ask_user_for` and any card a plugin's `asks` returns.
- The form's own schema and description say two or more, so the refusal is a backstop.
- A card of no writable fields is untouched: the fork, and the approval gate.
- A card whose single field is read-only is untouched: nothing is being asked for.
- **BREAKING** a skipped single value is asked in prose, where a second card stood.

## Impact

- `src/cora/engine/steps.py` — the rule, at both places a card is built for the reader
- `src/cora/engine/ask_tool.py` — the form takes two fields or more, and says so
- `tests/cora/engine/test_steps.py` — the rule, and the gate fixture it made illegal
- `openspec/specs/cards/spec.md` — one scenario says the opposite of the new behaviour
- `README.md`, `docs/happy-path.md`, `docs/how-to/write-a-plugin.md` — what a card is for
- Leaves alone: the `Card` shape, the page, the pause port, and every plugin's own code
