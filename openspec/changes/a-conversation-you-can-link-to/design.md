## Context

The page has one address for everything, so the conversation on it cannot be linked to
or reloaded into.

## The seam

- The address is an external store the page subscribes to, not state it mirrors.
- `useSyncExternalStore` over `hashchange` is that subscription, so one answer exists to
  which conversation is open.
- A copy in `useState` would be a second answer, and the two can disagree.

## The hash, not the path

- The built page is served by `StaticFiles(html=True)`, which answers 404 for an unknown
  path.
- `/c/<thread>` would therefore work only while the page was already open.
- A route that survives a reload is the whole point, so the hash carries it.
- The cost is an address with a `#` in it, which is the smaller loss.

## Two ways to write it

- Opening a conversation is a navigation and pushes an entry, so back returns.
- A conversation acquiring a name is not, and replaces the entry it stands on.
- Pushing there would leave a back button returning to the same page under no name.

## When a conversation becomes nameable

- Only an answer records a conversation: a paused turn is in no store, a failed one in
  no record.
- So the turn reports the thread it just recorded, and the page names it then.
- The report is re-checked against where the reader is.
- The re-read before it is awaited, and the reader can leave while it runs.

## The stow outranks the address

- A thread parked on its first question is listed under no session.
- The stow is its only route back; the address names something SESSIONS already lists.
- Between the two, the stow is what is lost, so it wins.
- Narrowing this to unlisted threads would need the page to know more, sooner.
- Whether the stowed thread ever answered is a round trip it does not have.

## What the address may hold

- Whatever sits in that slot goes into the path of a request.
- `..%2Fmemory` decodes to `../memory`, which resolves to a different endpoint.
- So the address is checked where it is read, and escaped again where it is used.
- Letters, digits and dashes: what both ways of minting a thread produce.

## Guards and diagrams

- No port, no guard, no generated diagram changes.
