## Context

The shell already knows which fields have a page and which conversation is pinned to
what; the notice is the one thing on that list it has never read. See proposal.md.

## Goals / Non-Goals

**Goals** — a field whose notice is written puts its own conversation on the screen.

**Non-Goals** — starting a conversation, which only a turn can pin. Reading a notice's
contents. Telling one writer from another.

## Decisions

**The shell reads that a notice was written, never what it says.**

- `{"workout":"running"}` is the trainer's vocabulary and the fitness plugin's alone, and
  a shell that branched on it would be a shell that knows one plugin's words.
- So the rule is about arrival: a field that speaks is a field asking for the screen, and
  what it wanted to say is between it and its own page.
- Rejected: a reserved key every notice may carry to ask for the screen — a second
  contract to keep true, answering a question one rule already answers.

**The first answer is a baseline, not an event.**

- A notice outlives the page that wrote it, so the one standing at load is last time's,
  and acting on it would drag the reader somewhere on every reload.

**It is a hook of its own beside the rails.**

- The rails are what the panels draw from; this changes which conversation is open, which
  is the shell's own state and the address's.
- Rejected: folding it into `useRails`, which every panel reads — a poll whose only
  output is a navigation does not belong in what draws the lists.

**Quietly, on failure.**

- A deployment where nothing answers is the normal one, and a banner per poll would be
  the page shouting about a feature the reader may not use.

## Risks / Trade-offs

- One request per field with a page every few seconds, forever — small, and only for
  fields that brought one.
- A notice written while the reader is deliberately elsewhere moves them, which is the
  trade the story asks for: a lifter mid-set is not going to navigate.
- Two conversations pinned to a field open the newer, which is a guess the shell makes
  rather than a thing the lifter said.

## Ports, guards and diagrams

- No port and no Python: the notice route is already there, and this only reads it.
- No guard: the browser tier is what proves a poll changing an address.
- No diagram changes: none of the six draws the shell.
