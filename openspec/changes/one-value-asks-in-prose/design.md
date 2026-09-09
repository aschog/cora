## Context

See proposal.md — Why. Two paths build a card for the reader: the engine's gate, running
a plugin's `asks`, and the ask step, reading cora's own form call. A third path puts the
effect proposal, whose card is read-only fields and no ask at all.

## Goals / Non-Goals

**Goals:**

- One rule, stated once, holding over a plugin's card and cora's own alike.
- A refusal the model can act on: it names the value and says to ask in prose.
- A refused card costs the call, never the turn.

**Non-Goals:**

- Changing the `Card` shape, the pause port, or anything the page draws.
- Teaching the page about single fields; no card of one arrives for it to draw.
- Screening what a plugin does inside its own `run`.

## Decisions

- The rule is a guard the two card-building paths call, not a fourth pause step.
- It raises `ToolRefusal`, which both paths already answer with a refused call.
- It counts writable fields, so a read-only card is not an ask and is left alone.
- Not in `Card.__post_init__`: a card is data a plugin may build for any reason, and a
  settled card read back from a checkpoint must reconstruct.
- Not one call site: the ask step never runs a plugin's `asks`, and the gate never reads
  a form call, so neither is on the other's path.
- `Proposed.card` stays off the rule's path, and the docstrings say so rather than
  claiming a single choke point the code does not have.
- The form's schema takes two fields or more, so a well-formed call cannot be refused by
  the rule: the model is bound where it reads, and the guard backs it up.

## Risks / Trade-offs

- A model that ignores the description spends a round on a refusal, and a model that
  never stops spends the budget — which ends the turn with an error, not an answer.
- So the rule is stated where the model reads: the form takes two fields or more, and
  the refusal names the value and says to ask for it in prose.
- A plugin whose schema has one property now gets no card, and must read the value out of
  the reader's next message; the how-to says so.
- The guard is on the engine's side of the seam, so a plugin cannot opt out — which is
  the point, and the cost is a plugin that wanted a one-box form cannot have one.
