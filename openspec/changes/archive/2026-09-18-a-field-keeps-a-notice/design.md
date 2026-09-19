## Context

A page is served under its field's name and talks to cora's API as the reader holds it,
but every route there answers a question the browser asked. See proposal.md.

## Goals / Non-Goals

**Goals** — one small live value per field, written from outside the browser and read
by the page, over the process that already serves both.

**Non-Goals** — a queue, a history, a subscription, or anything kept past a restart. A
notice is what is true now, and the page asks again when it wants to know.

## Decisions

**The notice is the frontend's, not the core's.**

- Nothing in a turn reads it, so a port, a `Host` method and a field on `App` would all
  be surface the domain never touches.
- It lives beside the route that serves the page, held for as long as the process is,
  and the Telegram frontend is right to have none.
- Rejected: a plugin registering an HTTP handler of its own — the smallest honest
  contract for that hands a plugin a request and a response, and the web framework with
  them, which the hexagon exists to keep out.

**Cora holds it opaque.**

- What a notice means is between whoever writes it and the page that reads it, so cora
  checks that it is a small JSON object and nothing further.
- One notice, replaced whole: a writer that wants two facts sends them together, and
  cora never has to say how two notices combine.
- The page is the memory. A notice it never saw is one it cannot recover, which is the
  ceiling a reader accepts for a value that is live rather than kept.

**Cora stamps the arrival.**

- A watch, a sensor or a phone has a clock of its own and no reason to share cora's, so
  the one time in a notice that anything can reason about is the one cora wrote.

**It is addressed under the field, beside the fields themselves.**

- `scopes` is already the word the API uses for a field, and a notice is a field's.
- A field of the running composition and no other, read per request like everything
  else, the plugins folder being live.

## Risks / Trade-offs

- A notice is readable and writable by whoever reaches cora, as a page directory is
  already served to whoever reaches cora — so a deployment that binds past loopback
  opens this with the rest of the API, and `CORA_HOST` is where that is decided.
- Held in memory, so a restart mid-workout loses the notice, and the page falls back to
  what it knows itself.
- A writer that posts faster than the page polls loses the notices in between, which is
  correct for a value that means "now" and wrong for anything that means "each".

## Ports, guards and diagrams

- No port, no engine, no assembly: nothing outside the React frontend changes.
- No new guard. The architecture guard already holds the layers this does not cross.
- No diagram changes: none of the six draws the frontend's routes.
