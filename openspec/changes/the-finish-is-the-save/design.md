## Context

The page saves twice: a JSON history in the browser feeds History and the next workout's
weights, and a Markdown upload feeds cora. See proposal.md — Why.

## Goals / Non-Goals

**Goals** — one copy, the field's, and the page reads it as the coach does.

**Non-Goals** — offline use, a page opened outside cora, editing a saved workout, the watch.

## Decisions

**The field is the history.**

- On open and after a save the page lists the field's documents and reads the dated ones
  by name, over the route the change before this one adds.
- The Markdown is read in the page by the grammar the page writes: a name line, a heading
  with the load, a set line.
- Rejected: the JSON beside the upload, which is the two copies this change ends.

**Last weight and reps come from the latest save that worked the exercise.**

- Matched by the exercise's name as the heading spells it, since the document holds no id.
- Rejected: an id of the plan's in the document, which puts a page detail into the log.

**The name carries the moment, then the workout.**

- Day, time, then the workout, and the moment alone when the sheet gave no name.
- A day's saves still sort by time, and the rail says which workout each was.
- The coach reads the day off the front of the name and lets the rest be anything.
- Rejected: the workout first, which breaks a day's order in the rail.

**A save that failed leaves the workout standing.**

- The session clears only once cora answered; otherwise the sets stay logged, the finish
  stays offered, and the strip says why.
- Outside cora there is no field to read or write, so the finish only says not saved.
- Rejected: the clipboard and the textarea, which were the second copy's last resort.

**Import and Export go.**

- With no page-side history there is nothing to carry between browsers; the field carries it.

## Risks / Trade-offs

- A field with many saves is read one request a save on open — a lifter's log is small.
- A workout logged while cora is down lives only in the open page until cora answers.
- The browser suite's failed-save test changes shape: no textarea, no storage, the
  session still standing.

## Ports, guards and diagrams

- Nothing of cora's changes: no port, no guard, no diagram. The page is the plugin's.
