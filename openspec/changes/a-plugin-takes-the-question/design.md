## Context

A plugin takes part in a turn at five points, and every one of them refuses or amends:
none can answer, so a question a plugin could settle from what it holds still costs a
model round. The only thing that ends a turn before the model is a refusal, which writes
nothing and records nothing. The walk is drawn from the code, and its guard reads the
steps the composition root names and the fork the runner declares.

## Goals / Non-Goals

**Goals:**

- A plugin answers a question in its field, and the turn spends no round on it.
- A taken turn is a turn: in the transcript, recorded, checked by the answer handlers.
- A broken or over-eager handler costs the turn nothing it would not have had.
- The drawing of a turn says where the fork is, as it says where every other one is.

**Non-Goals:**

- A handler that pauses the turn, or one that runs a tool; both stay the core's.
- Streaming what a plugin wrote; an answer that took no round arrives at once.
- Skipping the brief: the field is settled and stated first, and that is a store read.

## Decisions

- **A third kind of event beside refusing and amending: taking.** The first text back
  ends the dispatch and is the answer; nothing, blank text, a wrong type or a raise pass
  the question on, and a dispatch nobody took answers with nothing.
- **Offered at the work marker, not at a sixth named step.** The marker is where the
  rounds are entered, so a turn taken there enters none; the walk keeps its five names
  and no fork lands in the middle of it. A step before the brief would save a store read
  and cost a renamed walk and a mid-walk fork in the drawing.
- **The runner forks at the marker on one route the engine owns.** `Loop.opening` says
  whether a round is spent — into the rounds where nothing has answered this turn, out to
  the answer where something has. The router between rounds is untouched; the
  alternative was one router at two sites with a route map that fits neither.
- **What was taken joins the transcript as this turn's assistant message.** The route
  reads that message and the answer step settles it, so the answer is contributed once,
  where it always was, and the answer handlers, the citations and the recording see a
  taken turn as any other. A flag in the state would be a second thing to keep true.
- **The plugin's conversation state is bound around the handler, as the tool round binds
  it.** A plugin answering the reader stands where a tool call stands, and what it keeps
  travels back into the state the same way. Handlers at the other five points stay unbound.
- **The fork is drawn where the graph declares it.** The reading of the runner takes a
  second decision — the one at no named node is the marker's — and the round map wraps
  the rounds in it. A fork the source has and the drawing denies is what the generator
  refuses to draw flat.
- **Rejected: the model step skipping itself when an answer is present.** A step that
  sometimes does not do what it is named for is a switch nobody can read off the graph.
- **Rejected: a refusal at screening carrying the answer.** A refusal is what the reader
  reads, and nothing else: no transcript, no record, no answer handlers.

## Risks / Trade-offs

- **A system-wide taking handler takes every question of every field** → scope it; the
  how-to says so, and loading a plugin is the deployment's act, as with a screen.
- **The brief is built for a turn that never reads it** → a memory read and string work
  per taken turn, accepted against a sixth step and a mid-walk fork.
- **Nothing streams on a taken turn** → the page reads the answer off the finished turn's
  frame, as it does for a turn whose model wrote nothing.
- **A handler that keeps a value and then raises has kept it** → the binding is written
  back whatever the handler did, as the tool round writes back a failed call's writes.

## What it touches

- **Ports:** `Host` names the sixth event; `Loop` gains `opening` and the graph port the
  `ROUNDS` route. No adapter changes but the runner's one edge.
- **Guards:** `test_diagrams` reads the fork off the round map; the gate guard is
  unchanged, the tools having gained no edge.
- **Diagrams:** `round-map.svg` is redrawn with the fork; the others are unchanged.
- **Docs:** `happy-path.md` counts six points and says what the marker does;
  `write-a-plugin.md` gains the row and the rule.
