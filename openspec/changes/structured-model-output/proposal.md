## Why

A delegated loop answers in prose, so a caller needing a shape parses it and guesses
when the parse fails.

## What Changes

- `delegate` takes an optional schema, and answers with a value validated against it.
- A caller that passes no schema is unchanged: it reads the prose the loop wrote.
- The provider is asked to hold the answer to that schema, not merely told about it.
- A model that cannot be held to one refuses the call, naming itself.
- An answer that arrives unvalidatable refuses too, rather than being parsed loosely.
- A refusal reaches the plugin as a refusal, so nothing reads as an empty result.
- The travel planner's day shape is the first caller, and drops its own JSON parse.
- **BREAKING** a shape the planner cannot get is a failed tool call, where it was a
  plan with no days.

## Impact

- `src/cora/ports/host.py` — `delegate` gains the shape, and says what it answers with
- `src/cora/ports/chat_model.py` — a round may carry the schema it must satisfy
- `src/cora/engine/host.py` — the delegated loop asks its last round for the shape
- `src/cora/adapters/openrouter_chat_model.py` — the schema reaches the provider
- `plugins/travel/src/cora/plugins/travel/planner.py` — asks for its days, parses none
- `openspec/specs/plugins/spec.md` — the requirement a delegated loop is held to
- `docs/how-to/write-a-plugin.md` — what a plugin may ask a loop for
- `tests/cora/engine/`, `tests/cora/adapters/`, `plugins/travel/tests/` — the new rules
- Leaves alone: the turn's own rounds, the tool-call path, the gate, and every plugin
  that delegates for prose
