## Context

A turn is streamed to the page over SSE while a worker thread walks the graph behind it.

## The seam

- The seam is the streamed response itself: the generator that feeds the page is the one thing that knows a reader is still there.
- Its `finally` runs whether the reader pressed stop, closed the tab, or lost the socket, so one guard covers all three.
- What it sets, the worker's two callbacks read: a step reported and a piece written are the only places the turn touches the page.
- Either of them raising unwinds the round, closes the graph stream, and ends the thread — the path a failed turn already takes.
- No route is added and no registry of running turns is kept, because the connection is the registration.

## Where a turn notices

- At the next step, or the next piece of prose, whichever comes first — which on a streaming model is the next token.
- A turn parked inside one slow tool call notices when that tool returns, and that ceiling is left standing.
- Closing it would mean a cancellation token through every tool, which is a port change for a case a round boundary already covers.

## What a stopped turn leaves

- Nothing recorded: a turn is recorded when it is answered, and a stopped one never was.
- So the page draws it as it draws a failed one — the question, and a sentence where the answer would be.
- The half-written prose goes with it, because keeping text that no reload can bring back says the turn is there when it is not.
- The thread's checkpoint stands at the last completed superstep, so the conversation is asked in again as normal.

## The page

- The ask control becomes the stop control while a turn runs, rather than a second control beside it.
- One control, because asking and stopping are never both available: the composer is closed while cora works.
- The turn's `AbortController` lives with the turn in `useTurn`, which already owns what a turn writes to.
- An abort lands in the catch that draws a failed turn, so the stop costs the page no second path.

## Ports, guards, diagrams

- No port changes, no guard changes, no diagram is redrawn: nothing under `src/cora` is touched.
