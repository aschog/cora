## Context

A row shows `done/planned · weight` beside the exercise, and the browser suite reads
progress off it. See proposal.md — Why.

## Goals / Non-Goals

**Goals** — a row that is the exercise's name, and a suite that still sees progress.

**Non-Goals** — any change to the sets panel, where the count and the weight live on.

## Decisions

**The readout goes, and nothing replaces it.**

- A complete exercise still reads complete, which the row's own class already says.
- The suite reads progress off the set buttons marked done, which is what the lifter
  reads too.
- Rejected: a hidden attribute kept for the suite, which is the readout under another
  name.

## Risks / Trade-offs

- Which exercises are part-done is no longer visible from the list, only from the panel.

## Ports, guards and diagrams

- Nothing of cora's changes: no port, no guard, no diagram.
