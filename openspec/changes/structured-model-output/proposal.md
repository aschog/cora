## Why

A delegated loop answers in prose, so a caller needing a shape parses it and guesses
when the parse fails.

## What Changes

- `delegate` takes an optional shape, and answers with a value validated against it.
- A caller that passes no shape is unchanged: it reads the prose the loop wrote.
- The shape is put to the model as a schema it is held to — the loop is offered one more
  tool, `answer`, whose parameters are that shape.
- An answer that does not satisfy it is told to the loop, which corrects it in the rounds
  it already had.
- Prose where the shape was asked for, or an allowance spent without answering, refuses
  the call and says which.
- A shape that requires nothing of an answer is refused before a round is spent.
- The travel planner's day shape is the first caller, and drops its own JSON parse.
- **BREAKING** a day shape the model will not produce is a failed tool call, where it was
  a plan with no days.

## Impact

- `src/cora/ports/host.py` — `delegate` gains the shape, and says what it answers with
- `src/cora/engine/host.py` — the loop offers `answer`, and returns what it was called
  with
- `plugins/travel/src/cora/plugins/travel/planner.py` — asks for its days, parses none
- `openspec/specs/plugins/spec.md` — the requirement a delegated loop is held to
- `docs/how-to/write-a-plugin.md` — what a plugin may ask a loop for
- `tests/cora/engine/`, `tests/acceptance/`, `plugins/travel/tests/` — the new rules
- Leaves alone: the model port and its six implementations, the OpenRouter adapter, the
  turn's own rounds, the gate, and every plugin that delegates for prose
