## Context

The names view is one line per day, and nothing in it says which name is a workout,
which a lift, or that more is on file. See proposal.md — Why.

## Goals / Non-Goals

**Goals** — a names view a model cannot misread, and a brief that stops it filling gaps.

**Non-Goals** — a change to the detail view, the grammar, or what a save carries.

## Decisions

**The text says what it is.**

- Workouts come first on a day's line, and an untitled save's lifts follow, marked as an
  untitled save.
- A closing line counts the days and the saves and says where the numbers are, so "no
  sets in the log" has nothing to stand on.
- Rejected: a stricter brief alone, since the last one was already clear and was still
  read past.

**The brief forbids the gloss.**

- One sentence: answer with the tool's text, and add nothing about what the log holds or
  lacks.

## Risks / Trade-offs

- The closing line is a sentence the model may quote, which is the point.

## Ports, guards and diagrams

- Nothing of cora's changes: no port, no guard, no diagram.
