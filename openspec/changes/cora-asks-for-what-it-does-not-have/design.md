## Context

Cora's one asking tool settles a fact between values it already found, so an ask for
values nobody holds has no shape and comes out as prose.

## Goals / Non-Goals

**Goals** — one card for any number of values cora does not hold, raised by cora itself,
drawn by the renderer that already exists, and settled into the turn that asked.

**Non-Goals** — forbidding prose, which no library and no wording can do. Layout the
model dictates. Validation past the schema and the browser. A card raised by anything
but a call, which would be a handler stopping a turn.

## Decisions

**A second tool beside `ask_user`, not a wider one.**

- The two asks take different arguments: one offers values found, the other names values
  wanted.
- A model picks the tool whose shape fits, which is the choice it is good at.
- Rejected: one tool taking options or fields — a branchy schema is one a model
  half-fills, and neither description can then be sharp.

**The model names the fields, and cora builds the card from them.**

- What it declares is JSON Schema's own vocabulary — a description, a type, a `format`,
  a list of choices — so the page's control lookup needs no new row.
- The card is assembled by the same function a tool's card is, so the two cannot drift.
- Rejected: a fixed schema of the values cora expects, which cora cannot know.

**`AskStep` raises it, because it is the one step that can stop the run.**

- The router already sends a round's ask to that step ahead of the round's tools, and it
  sends either ask by the same rule.
- The one-ask-a-turn guard is that rule, so it covers the new tool by standing still.
- Rejected: the gate, which fills in a call's own arguments — here the arguments are the
  question, not the thing being filled.

**What the reader wrote comes back as that call's result.**

- The model reads it as it reads any tool result, so no round is forged into the
  transcript to carry it.
- A reader who writes nothing settles it too, and the result says so — the same way a
  declined effect is answered.

**No new domain type: the tool builds a `Card`.**

- A card is already an `Asks`, so a prompt and fields need nothing wrapped around them.
- Rejected: a third shape beside `Decision` and `Proposed`, which would hold what a card
  holds and add a name.

**Cora's own, offered from the assembly.**

- It stands beside `search_documents`, `remember` and `ask_user`, so a deployment with
  no plugin loaded can ask.
- Rejected: a system-wide plugin — the contract allows it, but it splits asking across
  the core and a package nobody may load.

**An ask cora cannot read is refused where it was made.**

- An ask naming no field is answered to the model, like any malformed call, rather than
  put to a reader as an empty card.

## Risks / Trade-offs

- The model may still answer in prose → the tool removes the reason rather than the
  possibility, and the trace says which it chose.
- Two asking tools to pick between → each description names the case it is for, and the
  wrong pick costs a round rather than the turn.
- A model may ask for what it could have inferred → the description forbids asking what
  it can look up, as `ask_user`'s already does.
- A card of many fields is a wall of controls → the description asks for the fields the
  answer turns on, and no more.

## Ports, guards and diagrams

- No port changes: the pause port already carries a card out and a record back.
- The plugin contract's version is untouched — this adds nothing a plugin declares.
- No diagram is regenerated: no domain type is added and no step is renamed.
