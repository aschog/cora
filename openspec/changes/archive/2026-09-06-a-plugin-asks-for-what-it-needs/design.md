## Context

Two pause shapes reach the page and the page draws a component for each, so a third
shape is a third component only this repository can add.

## Goals / Non-Goals

**Goals** — one card shape the backend writes, one renderer the page keeps, a field
whose control follows from its schema, and a plugin that asks without touching TypeScript.

**Non-Goals** — a plugin shipping its own React, which is a fork by another name.
Layout a card can dictate, deferred until a card needs one. Validation beyond what the
schema and the browser already do. A card raised outside a paused turn.

## Decisions

**The card is the one abstraction, and the two existing pauses become producers of it.**

- `Pending` carries a card, so its exactly-one-of check dissolves rather than growing a
  third arm.
- `Decision` and `Proposed` stay as they are and gain a card view, so the engine keeps
  its vocabulary.
- Rejected: a third `Pending` arm — a shape whose validity is a count of nulls does not
  survive a fourth kind.

**A card is a prompt, fields and actions, and nothing else.**

- A field is a name, a JSON Schema, a value already known, whether the reader may write
  it, and whether it is required.
- An action is a label, a note, whether it waits for the required fields, and what the
  card says once it was taken — carried by the action, because only whoever offered it
  knows what taking it meant.
- A decision is no fields and one action per option; a proposal is read-only fields and
  two actions.
- Rejected: booleans on the card for read-only, reopenable and submit-on-pick — flags
  re-deriving what fields and actions already say.

**The control follows from the schema, through a lookup the page reads.**

- Type, `format` and `enum` pick the control; an unmatched schema falls back to text.
- A new kind of field is a row in that lookup, which is the extension point the north
  star asks for.
- Rejected: a card naming its widgets — a second vocabulary the schema would have to
  agree with.

**Resuming carries the action and the values.**

- `POST /api/resume` takes the action taken and a record of what was written, replacing
  the bare label, and `POST /api/approve` goes with the shape that needed it.
- One pause port over every stop, handed that record back, so the engine reads values
  rather than parsing a string.
- An approve action carries the call's own id, so two effects of a round still cannot
  settle each other, and `Approval` is a type nothing needs any more.
- The route drops a value for a field the card marked read-only, so a request cannot
  rewrite the argument it is approving.
- Rejected: JSON inside the label — a wire that lies about its shape, and a parse that
  can fail where a type could not.

**A card is data across the boundary, and a closure only inside the page.**

- What crosses the wire has no callbacks; the page turns each action into a call to
  `resume`, and draws every part of a card as text rather than evaluating any of it.

**A tool declares what it asks for, and the gate puts it.**

- `Tool.asks` is handed the arguments as written and answers with a card, or with
  nothing to run as called — one field on the shape a plugin already fills in.
- The gate does the putting, because it already runs no tool and is already the only
  path from the model to them; filling in happens ahead of the proposals, so a call that
  both asks and acts is approved as it will really be made.
- What the reader wrote is contributed as state keyed by the call it belongs to, not
  written into the transcript: an assistant message cora forged would read as a round
  nobody spent, and `_requested_calls` is the one place the round is read.
- Travel's searches build their card from the schema `trips.py` already generates, so
  the card and the query cannot drift.

## Risks / Trade-offs

- `POST /api/resume` changes shape, and it is cora's own page that calls it — no
  deployment carries a second client.
- A schema-driven control is less exact than a hand-built one, and the fallback to text
  is what keeps an unknown schema usable rather than pretty.
- The travel card can ask for values the model could have inferred, so the tool asks only
  when the route or the window is absent.

## Ports, guards and diagrams

- `cora.ports.pause` changes: what a pause is handed back is a record, not a label.
- No new port, and no change to the plugin contract's version — a card is built from a
  tool's existing schema.
- The domain class diagram and the round diagram are regenerated.
- The architecture guard gains one line: a protocol states a shape and holds no data.
