## Context

A plugin reaches the turn and nothing else, so a field whose subject wants a surface
has none. See proposal.md — Why.

## Goals / Non-Goals

**Goals** — one more kind of registration, a directory served under a path naming the
field, and one answer saying which field has a page.

**Non-Goals** — where a shell draws a page, which is the next change. A page taking part
in a turn, which is what a tool is for. A page for every turn, and a second one for a
field. Containing what a page's script may call, which nothing about a plugin is
contained in today.

## Decisions

**A fourth kind, and the value is the directory.**

- `Registration` carries a kind and a value already, and `Contributed` is one shape over
  every kind, so neither widens.
- The engine holds the path it was handed and never a URL: an HTTP path is the
  frontend's to compose, and a resolved one would not be the plugin's own any more.

**The field is required, where every other registration may be system-wide.**

- A page belongs to a subject, and a page for every turn is a second cora.

**The app carries one map from field to directory, as it already carries the fields.**

- `assemble` derives it from the registry the way it derives the fields on offer, and it
  is the only thing about a page that crosses into a frontend.
- One page per field then *is* the map: two plugins under one field cannot both be in it,
  so the collision and the carrier are one thing, refused as two tools of one name are.
- The listing says a plugin brings a page and for which field, and no host directory
  reaches the screen — a name of its own is what a tool has and a page has not.

**Registering checks the field, and nothing on disk.**

- A composition that raises refuses *every* request until the folder is mended, and the
  folder's signature reads only Python files — so a deleted page directory would take
  cora down at the next unrelated edit rather than when it went.
- Rejected: refusing at load as an invalid schema does — a schema is a value in memory,
  and a directory is a fact that changes after any check.

**One route carrying the field's name, placed before the shell's own.**

- The route list is fixed when the app is built and which plugins are loaded is a fact of
  the request, so the route names no field and resolves one per request.
- The field is looked up in the map and never used as a path, which is how deleting a
  plugin by name already refuses a name that is a path.
- The reported path ends in a slash and is the one that answers: the slashless form falls
  through to the shell, as every other unknown path does.

**The static server does the file work, told not to check its directory.**

- Normalising, resolving both ends before the containment check, the entry page, `HEAD`,
  the method refusal and the revalidation are all its own.
- It is built to check its directory once and raise afterwards, which would answer a live
  folder's deletion with a crash — so that check is off and a missing one is a refusal.

**Served as it is on disk, and the browser told so.**

- A response carrying only a modification time may be reused without asking, which would
  make a live folder a lie one cache deep — so a page asks to be revalidated.

**Which field has a page rides with the fields, not with the pin.**

- The shell knows its fields before a conversation has one, and a page the reader can
  only see after a turn is a page they cannot start from.

**Same origin, deliberately, and the disclosure page carries it.**

- The page is served by the cora the reader is already running, so it calls the API as
  the reader holds it and no token is minted for it.
- That makes one of the page's claims false: the approval gate still runs, but a page can
  read a waiting card and answer it, so the yes need not be the reader's.
- Rejected: containing the frame — the same origin is what buys the token-less call and
  the browser's own sensors, and the only whole boundary costs both.

## Risks / Trade-offs

- A page is as trusted as the plugin that brought it, and adds three things its Python did
  not have: the browser's sensors and storage, the reader's own network position, and a
  column of the screen to draw in.
- Everything under the registered directory is public on an unauthenticated port, so a
  plugin publishes whatever it puts there, and a symlink out of it is simply not followed.
- A shell build shipping its own top-level directory of that name would be shadowed by the
  route, which no build does today.

## Ports, guards and diagrams

- `Host.register_page` is added surface, so `CONTRACT` stands where it is.
- No new port and no new adapter, so the component map and the domain map are unchanged.
- The packaging guard is where a plugin shipping files that are not Python gets covered,
  which the plugin bringing the first page will need.
