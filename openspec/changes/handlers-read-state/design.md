## Context

`keeping.bound` wraps a tool call and nothing else, so a plugin's own code runs in two
places with two different views: inside a tool it reads what it kept, inside a handler
it reads nothing. A field that puts a word with a tool cannot, at answer time, ask
whether the answer is that word.

## Goals / Non-Goals

**Goals:**

- A handler on the answer reads and writes the plugin's conversation state.
- One rule for where a plugin's code runs: bound alike, whichever door it came in by.

**Non-Goals:**

- The other four events. Screening runs before there is a turn to keep for, and the
  three in the round are already inside the binding.
- Handing a handler the tool calls of the turn; what it needs of them it reads back.

## Decisions

- **Bind in the answering step, not in `dispatch`** — `dispatch` has no state to bind,
  and the round already binds around it; the step is where the state is.
- **Hand `kept` back from the step**, as the tool round does, so a handler that kept
  something has kept it.

## Risks / Trade-offs

- **A handler now has a way to change the next turn**, which is what a plugin
  correcting its own drill needs and what a careless one could misuse; it is the same
  power a tool already has.

## What it touches

- **Ports:** none.
- **Guards:** none.
- **Diagrams:** none.
- **Docs:** `docs/how-to/write-a-plugin.md`, one clause on where `cora.state` is bound.
