## Context

Finishing checks for a logged set and warns when there is none, and the watch finishes
the same way without a button. See proposal.md — Why.

## Goals / Non-Goals

**Goals** — a finish that cannot be pressed for nothing, under a shorter name.

**Non-Goals** — the watch's finish, which keeps its guard and its warning.

## Decisions

**The button follows the session.**

- Each render sets it enabled when any set is logged, so it wakes with the first set and
  sleeps when a new workout starts.
- The guard inside finishing stays, for the watch and for a tap that beats a render.
- Rejected: hiding the button, which moves the header about as sets are logged.

## Risks / Trade-offs

- A disabled button explains nothing, and the empty sets panel is the explanation.

## Ports, guards and diagrams

- Nothing of cora's changes: no port, no guard, no diagram.
