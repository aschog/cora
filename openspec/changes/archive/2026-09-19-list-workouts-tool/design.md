## Context

The trainer writes the grammar `train` reads, the tool it was ported from outside this
repository. `train stats` already answers the two questions a log is asked. See
proposal.md — Why.

## Goals / Non-Goals

**Goals** — the log read back as numbers, by one tool the coach calls for what was
trained.

**Non-Goals** — bodyweight from a profile, heart-rate lines, charts, writing the log, or
a multilingual embedder.

## Decisions

**The read side of `train` comes across, and the store stays behind.**

- The parser and the two read use cases are pure functions over text, ported as they are.
- The store, git and the server are what cora already is: the document store, the upload
  and the rail.
- Rejected: a table of sessions the plugin keeps, a second place the training lives,
  unseen by rail and search.

**One tool, two filters.**

- `list_workouts` takes an exercise and a day, covering "all of it", "this lift over time"
  and "lately".
- Rejected: two tools mirroring `train stats`'s two modes, because the model picks a
  filter better than a tool.

**A day is a session.**

- Documents of one day merge in upload order, as `train` appends into one file.
- A save from the wrist and a save from the page are one day's work.
- A document not named for a day is a plan or a guide, and is not listed.

**The numbers are the tool's, and bodyweight is not guessed.**

- Reps and volume come from the tool, because the brief forbids the model the arithmetic.
- A bodyweight load has no volume rather than a wrong one, there being no profile to read.

**Rose or not is said per movement.**

- Compared against the previous session of that exercise, as `train` marks ↑, so
  progression is read, not reckoned.

**A name is a name, whatever its script.**

- A heading is a name and a load, and the parser reads the load in any script.

**A document the grammar refuses is skipped.**

- One bad file should not empty the list, and the trace says which one through `cora.show`.

**The brief routes the question.**

- The coach lists for what was trained and searches for what a guide says, in one added
  line.

## Risks / Trade-offs

- The whole field is read on every call, and `since` narrows what is answered, not what
  is read.
- Fields are a few hundred small files at most, so that is cheap.
- The trainer's grammar and the parser live in two files, one JavaScript and one Python.
- The outer test posts what the trainer writes, which is what holds them together.
- A timed set reads as its reps, as `train` reads it, and the trainer writes none.

## Ports, guards and diagrams

- No port of cora's changes: the plugin uses the listing the core change hands it.
- Guards: none new, and the wheel guard already covers a new module of a plugin.
- Diagrams: none draws a plugin's tools, so nothing regenerates.
