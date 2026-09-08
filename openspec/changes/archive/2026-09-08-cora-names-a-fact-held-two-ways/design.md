## Context

The brief lists remembered facts flat and `ASK_RULE` asks the model to spot a conflict
among them; three models were run against three bodyweights and each failed differently.

## Goals / Non-Goals

**Goals:**

- Move the noticing from the model to cora, and leave the judging with the model.
- Say the conflict where the facts are stated, so the two are read together.
- Cost nothing where there is no conflict.

**Non-Goals:**

- Deciding which value is current — that is the reader's, and the ask tool is how it is put to them.
- Understanding a contradiction in prose, which needs a reader rather than a rule.
- Changing what a fact is: no subject field, no schema, no migration.

## Decisions

- The section is built in the focusing step beside the facts it is about, because the conflict is a reading of that list rather than a step of its own.
- Detection is lexical — the words before a fact's first figure — so it needs no model call, no clock and no store change.
- A conflict is stated, never acted on: raising the card here would ask about a fact the question may not turn on, which is the over-asking the brief already forbids.
- The heuristic's ceiling is written where it is taken, as a `ponytail:` comment naming what it misses and saying to widen it on a real case rather than a guessed one.

## Risks / Trade-offs

- Numeric-only detection finds a disputed weight and misses a disputed diet; the alternative is a subject on every fact, which is a contract change across the port, the tool, the store and the rail.
- Two notes that share opening words but are not one subject would be reported as a conflict; the cost is one line of brief the model can dismiss.
- The model may still raise a form instead, where a question also turns on values nothing holds — measured, and recorded in the live test rather than asserted.
- Ports, guards and generated diagrams are untouched: this adds no class, no slot and no node.
