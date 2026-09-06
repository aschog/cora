## Why

A row the reader confirmed away stays listed until the store answers, so the click reads
as having missed.

## What Changes

- A document, a conversation or a fact goes from its rail the moment the reader confirms
- Forgetting everything empties the memory rail the same way
- A delete the store refuses puts the row back, with the sentence saying why
- A row coming back is never the only account of what happened
- What went through is confirmed by reading the listing again, not by the page's guess
- What went through also clears what the page last could not do, as an upload does
- Capabilities `documents`, `sessions` and `memory` gain when the row leaves the list

## Impact

- `frontends/react/ui/src/hooks/useRemoving.ts` — new, one mutation over all four deletes
- `frontends/react/ui/src/App.tsx` — each rail says which listing its row leaves, and how
- Left alone: the API, which is asked exactly what it was asked before
- Left alone: what each question says is lost, which is the card's and not the delete's
- Left alone: which deletes are refused, and the conversation in use that refuses one
- Left alone: the stow, which is let go with the conversation it was left in
