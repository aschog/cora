## Why

A turn that needs five values from the reader can only offer labels to click, so a
plugin wanting a filled-in form has to fork the page.

## What Changes

- A paused turn reaches the page as one card: a prompt, fields to fill, and actions to take
- The card is data the backend wrote, so a plugin adds one without touching the frontend
- A field carries its JSON Schema, and the page draws the control that schema describes
- An action says what it is called and what it settles, and may require the fields be valid
- A decision is a card with no fields, and a proposal is a card whose fields are read-only
- The page keeps one renderer, so a new kind of field is a case there and never a component
- Resuming a paused turn carries the values the reader wrote, not only a label
- **BREAKING** `POST /api/resume` takes an action and a record, and `POST /api/approve` goes
- A tool declares `asks`, and the gate puts the card and fills the call in before it runs
- The travel scope asks for the trip before it searches, as fields rather than a sentence
- New capability `cards`, which says what a paused turn is and how it is put to the reader

## Impact

- `src/cora/domain/decision.py` — the card shape, and `Pending` carrying one instead of two
- `src/cora/domain/approval.py` — a proposal describes itself as a card, and `Approval` goes
- `src/cora/domain/agent_state.py` — what the user filled in, by the call it belongs to
- `src/cora/ports/plugin.py`, `src/cora/ports/host.py` — a tool may declare what it asks for
- `src/cora/ports/pause.py` — what a pause is handed back is a record
- `src/cora/engine/ask_tool.py`, `src/cora/engine/steps.py` — a decision is built as a card
- `frontends/react/src/cora/frontends/react/payloads.py` — the card over the wire
- `frontends/react/src/cora/frontends/react/api.py` — `/api/resume` widened, `/api/approve` gone
- `frontends/react/ui/src/components/` — one card component, replacing two
- `plugins/travel/src/cora/plugins/travel/trips.py` — the search asks for its own fields
- `README.md`, `docs/how-to/write-a-plugin.md` — that a plugin can ask for what it needs
- Left alone: the gate, which still stops every effect and is still cora's own
- Left alone: what a tool declares, and the schema it already ships
- Left alone: the trace, the citations and everything a turn that does not pause does
