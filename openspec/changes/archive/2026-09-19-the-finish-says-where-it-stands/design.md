## Context

The strip carries every line worth one, a save that worked was one of them, and the
button is disabled or not and says Finish either way. See proposal.md — Why.

## Goals / Non-Goals

**Goals** — one control that says what the workout is waiting for, and a quiet strip.

**Non-Goals** — the strip's other lines: a refused save, an unreachable sheet, the watch.

## Decisions

**The button has three faces.**

- Nothing logged: a grey pill reading "no sets logged yet", a tap for an icon, disabled.
- A set logged: the blue "Finish", enabled.
- Cora took the save: a blue pill reading "saved", a check for an icon, disabled, until
  the next set is logged and it becomes "Finish" again.
- Rejected: a fourth face for a refused save, which the strip already says in words.

**Silence is the success.**

- The strip clears when cora takes the workout, and keeps the watch's line when the
  watch ended it, since that is the one thing the lifter cannot see from the wrist.
- The browser suites read the button, which is what the lifter reads.

## Risks / Trade-offs

- Between the tap and cora's answer the button reads "no sets logged yet", for as long
  as the upload takes.

## Ports, guards and diagrams

- Nothing of cora's changes: no port, no guard, no diagram.
