## Context

Three rails offer the same act — delete a row the reader has confirmed — and each waited
for a round trip before the list showed it gone.

## The seam

- The listings are held under keys, so the row leaves by writing the held listing.
- One mutation over all four deletes, taking what leaves and which listing it leaves.
- Four would be four places for the rollback to be written differently.

## What a call site says

- The request that takes it away, the listing it is drawn from, and that listing without
  it.
- The last is what lets the row go before the store has been asked.
- It is also what puts it back, because what was there is kept first.

## The order

- Reads already on the wire are called off, or one would land and undo the removal.
- What was held is kept, then the listing is written without the row.
- Refused: the kept listing goes back, and the sentence says why.
- Either way the listing is read again, so the store confirms it rather than the page.

## Two sentences that must not clear each other

- The re-read afterwards is the rails' own, not the page's.
- The page's also lets go of what it last could not do, which is the sentence just
  written.
- So a rollback keeps its explanation, and a delete that went through clears the page's
  last complaint.

## What this does not change

- Which deletes are refused, and what each question says is lost, are untouched.
- A row reappearing is never the only account: the sentence arrives with it.

## Guards and diagrams

- No port, no guard, no generated diagram changes.
