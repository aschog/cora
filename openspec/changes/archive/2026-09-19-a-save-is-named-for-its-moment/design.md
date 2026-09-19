## Context

The trainer names a save for the day, the store keeps every upload apart by its bytes,
and the listing merges a day's documents in upload order. See proposal.md — Why.

## Goals / Non-Goals

**Goals** — one rail entry per save, and a day's saves in the order they happened.

**Non-Goals** — renaming what is already saved, a time zone other than the browser's,
or a session split finer than a day.

## Decisions

**The moment is in the name, day first.**

- `YYYY-MM-DD-HH-MM-SS.md` sorts by time as text and still starts with the day the
  listing keys on.
- Dashes rather than colons, because the store would turn colons into dashes on disk and
  the rail would then show a name no file has.
- Local time, as the day already is: a workout belongs to the lifter's evening.

**The listing reads the day and orders by the name.**

- The name's grammar grows an optional time, so a save named the old way still lists.
- Documents sort by name before a day's are merged, stably, so two of one name keep
  their upload order.

**The page's naming is held by reading the page.**

- The plugin's suite reads the function that names a save, as it reads the hosts the
  page reaches; the browser tier posts a real save and matches the pattern.

## Risks / Trade-offs

- Two saves within one second share a name, and the store keeps them apart all the same.
- Saves already on disk keep their day-only names, and list as they did.

## Ports, guards and diagrams

- Nothing of cora's changes: no port, no guard, no diagram.
