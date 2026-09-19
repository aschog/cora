## Context

The tool returns JSON and the brief says to read its numbers, so the model renders a
table and names the exercises in its own words. See proposal.md — Why.

## Goals / Non-Goals

**Goals** — the answer to "what did I train" is short, and every character of it is the
tool's.

**Non-Goals** — charts, totals across days, a second tool, or a change to what is logged.

## Decisions

**The tool renders, the model relays.**

- Text the model can quote leaves it nothing to lay out, as `train`'s reporter did for a
  terminal.
- Rejected: JSON plus a stricter brief, because a model shown numbers makes a table of
  them.

**Two views on one parameter.**

- `detail` is off by default: one line per day, the exercises worked, each named once.
- On, each movement is a line with load, sets, reps, volume and a mark where it rose.
- Rejected: a second tool for detail, since the filters are the same and the model picks
  a flag as easily.

**Names as the log spells them.**

- The line carries the heading's name untouched, and the brief says not to translate it.

**The filters hold in both views.**

- An exercise or a day narrows the sessions before either rendering.

## Risks / Trade-offs

- A model may still rephrase, and the brief is the only hold on that.
- The middle dot separates names, because names carry commas and full stops of their own.

## Ports, guards and diagrams

- Nothing of cora's changes: no port, no guard, no diagram.
