## Context

The page has one upload path, held by `useDocuments` and drawn once, in the rail over
the list it changes. See proposal.md — Why.

## Goals / Non-Goals

**Goals** — the same upload reachable from where the reader is typing.

**Non-Goals** — a second upload path, a second place news is drawn, and anything about
what a photo is before it is kept.

## Decisions

**One upload, drawn twice.**

- The composer's control calls the hook the rail's control calls, so there is one place
  a file is refused, indexed and announced.
- Rejected: an upload of the composer's own — two paths to one API is where a refusal
  gets reported in one place and not the other.

**A control, not a menu.**

- cora has one thing to add, so a menu would be a click in front of a file picker.
- A menu is what this becomes when there is a second entry to put in it, and the
  control is the same button either way.

**News stays where the list is.**

- What an upload did is drawn beside the list it changed, which is the rail — the
  composer's control says only what it is doing, and the field's documents say the rest.
- Rejected: a notice over the conversation, which would say the same thing twice.

## Risks / Trade-offs

- Two controls for one act → they are drawn differently and stand in different places,
  and the rail's is the one with the list under it.
- An upload started from the composer while the rail is folded is news the reader may
  not see → the control itself says it is running, and unfolding shows the list.

## Ports, guards and diagrams

- No port and no core change: the API this uses is the one the rail uses.
- No guard changes and no diagram changes: nothing about the composition moves.
