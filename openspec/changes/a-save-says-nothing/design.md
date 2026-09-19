## Context

The strip carries every line worth one, and a save that worked was one of them. See
proposal.md — Why.

## Goals / Non-Goals

**Goals** — a quiet save, and a suite that still sees it landed.

**Non-Goals** — the strip's other lines: a refused save, an unreachable sheet, the watch.

## Decisions

**Silence is the success.**

- The strip clears when cora takes the workout, and keeps the watch's line when the
  watch ended it, since that is the one thing the lifter cannot see from the wrist.
- The browser suite waits for the upload's response and reads the field, which is what
  a save is.

## Risks / Trade-offs

- Nothing says the save landed, and the History and the rail do.

## Ports, guards and diagrams

- Nothing of cora's changes: no port, no guard, no diagram.
