## Context

The port dropped the sheet sync with the rest of the tool's own plumbing. Everything
else it dropped was something cora answers; this was not. See proposal.md — Why.

## Goals / Non-Goals

**Goals** — the plan read from the sheet on every open, degrading to what was last read
and then to what the page ships with.

**Non-Goals** — cora reading the sheet on the page's behalf. A sheet per reader, which
is an edit to the page. Writing to the sheet, which the workout does not do.

## Decisions

**The page asks the sheet itself.**

- A published sheet answers any origin, which is what made the old JSONP fallback a
  `file://` workaround and nothing more — served over HTTP there is nothing to work around.
- Rejected: the plugin fetching it and handing it over — the page has no way to ask a
  plugin for anything, and giving it one is a seam this needs no part of.

**It degrades twice rather than failing once.**

- What was last read is kept, so a gym with no signal trains from the plan it had.
- The plan in the page is the floor, which is why it stays in the coach's own language:
  it is what a reader with no sheet of their own is left with.

**The sheet is named in the page, and that is how it is changed.**

- The page is the plugin's own file, and a plugin's settings are the deployment's to
  read — not a static page's, which is handed to a browser exactly as it sits on disk.

## Risks / Trade-offs

- The shipped page names one person's sheet, so anyone else running the plugin trains
  from it until they edit the file.
- The exercise names are the sheet's, so a sheet written in another language is the log
  cora is then asked about in whichever language the reader asks in.
- The plan changes under a workout that is already running, which is what keeping the
  progress of the exercises that survive is for.

## Ports, guards and diagrams

- No port, no core change, no API: the page fetches, as it always did.
- The plugin's own suite holds the hosts the page may reach, and the sheet is now one.
- The browser tier never reaches it: the parsing is exercised on a string, and the rest
  of the suite runs as a reader with no signal does.
