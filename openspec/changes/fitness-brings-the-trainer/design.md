## Context

The seam and the screen are both finished, and no plugin uses either. The trainer this
brings over already exists, outside this repository, built around a server of its own.
See proposal.md — Why.

## Goals / Non-Goals

**Goals** — the trainer as the fitness field's page, and a finished workout landing in
that field as a document cora can answer from.

**Non-Goals** — reading the log back as numbers, which is a change of its own. The watch,
the plan sheet and the offline build, which belong to the tool it came from. A second
field, or anything the other plugins can see.

## Decisions

**Only the page comes across.**

- What it was built around — a local server that commits to git, a watch listener, a
  spreadsheet the plan was synced from, a build that inlines everything for `file://` —
  are four answers to problems cora already answers, and each would arrive as a second
  way to do something.
- So the port is a subtraction: the same page with its own outside connections removed
  and one of cora's put in their place.

**The workout is a document, not a store of its own.**

- A field's documents are what cora searches and cites, so a workout written there is
  answerable the day it is written with nothing else built.
- Dated, because a session is a day's work and the reader asks about days.
- Rejected: a tool that keeps a log — a plugin's own store would be a second place the
  reader's training lives, invisible to search and to every rail that lists what they have.

**The page reads its own field out of where it is served.**

- It is at the path its field is named by, so it uploads into that field without the
  plugin writing its own name into a file the plugin also names.
- Same origin, so the upload is the reader's own API call and carries nothing.

**The plan is the page's, and stays in the file.**

- A sheet somewhere else is a dependency the reader cannot see and cora cannot serve.
- Editing the page is how the plan changes, which is what a plugin's own files are for.

**What it fetches for clips and tracking is named rather than hidden.**

- The exercise clips and the pose runtime come from the services they came from, so the
  trainer needs a network for those and says so — the page is the plugin's, and what a
  page fetches is the plugin's, which the disclosure page already states.

## Risks / Trade-offs

- The trainer is a large single file of someone's own JavaScript, and cora holds it
  without understanding it: what it draws is not held by any test of cora's.
- Its history lives in the browser's storage, so a workout finished while the upload is
  refused is only in that browser until it is copied out.
- Two workouts on one day are two documents of one name, which the store keeps apart and
  the rail lists once.
- The plan ships as part of the plugin, so changing it is editing a file rather than a
  setting.

## Ports, guards and diagrams

- No port and no core change: `register_page` is what this uses.
- The packaging guard grows to cover the files a plugin ships that are not Python, which
  this is the first of.
- No diagram changes: nothing about the composition moves.
