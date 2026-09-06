## Why

Cora can put two remembered weights to the reader, but has no way to ask for four
values nobody holds, so it asks in prose.

## What Changes

- Cora offers a second asking tool, for values it does not have and cannot look up
- The model names the fields it needs, and the reader is put one card of them
- A field may carry a type, a format and a list of choices, so a date is a date picker
- What the reader writes comes back as that call's result, and the turn answers on it
- A reader who fills in nothing settles the ask, and the turn answers without the values
- One ask a turn still, whichever of the two tools raised it
- Asking stays cora's own, so a deployment with no plugin loaded has this
- The travel scope needs nothing: the model reaches this where a search would not fit
- Modifies capability `cards`, which says what a paused turn puts to the reader

## Impact

- `src/cora/engine/ask_tool.py` — the second tool, its schema, and the card it builds
- `src/cora/engine/steps.py` — `AskStep` settles either ask, and the router sends both
- `src/cora/app/assembly.py` — the tool is offered beside cora's other own tools
- `README.md`, `docs/big-picture.md`, `docs/happy-path.md` — that cora asks for values
- Left alone: `ask_user`, which still settles one fact between values cora found
- Left alone: the gate, `Tool.asks`, and everything a plugin's own card already does
- Left alone: the card shape, the wire and the page — the renderer draws this already
- Left alone: the trace, the citations, and every turn that stops for nothing
