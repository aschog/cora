## Context

The tab's name is not in the CSV's cells, and the published HTML that shows it sends no
CORS header, so the browser may not read it there. See proposal.md — Why.

## Goals / Non-Goals

**Goals** — a save that says which workout it was, and a listing that says it back.

**Non-Goals** — a second request to Google, a name for the plan written into the page, or
renaming what is already saved.

## Decisions

**The name comes off the CSV response the page already reads.**

- Google names the export `<document> - <tab>.csv` in `Content-Disposition`, and exposes
  that header to any origin.
- The page decodes the `filename*` form, drops the extension, and keeps what follows the
  last dash.
- Rejected: fetching the published HTML for the tab list, which no origin may read.
- Rejected: a name typed into the page, which the sheet would then disagree with.

**The name is the save's first line.**

- A title line above the headings is how a Markdown document names itself.
- The grammar takes one such line and refuses a second, so a stray paragraph is still an
  error.
- The embedded plan has no sheet and so no name, and a save of it stays untitled.

**A day is named by its workouts.**

- The names view lists a day's workout names, each once, and an untitled save's
  exercises in their place.
- The detail view puts the names on the day's line, after the date.
- The exercise filter narrows the movements and leaves the day's names as they are.

**The page keeps the name with the plan.**

- Cached beside the plan, so a save made offline carries the name last seen.

## Risks / Trade-offs

- A document renamed in Google renames the workout, which is the point.
- Google could stop sending the header, and a save would then be untitled, not lost.

## Ports, guards and diagrams

- Nothing of cora's changes: no port, no guard, no diagram.
