## Context

A conversation lives in two stores at once — the turns a reader comes back to, and the
LangGraph thread the model answered on — and nothing today deletes either.

## Goals / Non-Goals

**Goals** — one call that drops both halves, a delete that is done rather than refused
when there is nothing to drop, and a list that cannot delete the conversation it is
being read through.

**Non-Goals** — deleting every conversation at once. Deleting one turn out of a
conversation. A dialog over the page, which the gesture below stands in for. Editing a
conversation's opening line, which is what a tidier list would otherwise want.

## Decisions

**Both halves are dropped by one call, and `Agent` is where it lives.**

- `Agent` already holds the runner and the conversations slot, and nothing else holds both.
- A frontend asks once, so no frontend can delete a conversation's record and leave its thread.
- The optional slot reads as it already does: no store is nothing to drop, not a failure.
- Rejected: the route calling both stores — the invariant would then be written once per frontend.
- Rejected: a use case of its own beside `Agent` — one method on the class that answers
  turns is smaller than a second component holding the same two slots.

**Each store's port gains a verb, rather than a new port over the two.**

- `Conversations` gains one beside `record`, `turns` and `sessions`.
- `GraphRunner` gains one beside `pending` and `pinned`, which already read a thread from
  outside a turn.
- Rejected: one "sessions" port over both — the two are bound separately in assembly, and
  a port spanning them would own both bindings.

**The thread's state is dropped through the checkpointer's own delete.**

- `BaseCheckpointSaver.delete_thread` is on every saver, so the memory one and the file
  one both answer it.
- cora writes no sql against LangGraph's tables, whose shape is LangGraph's business.

**The thread goes first, the record last.**

- A delete that fails halfway then leaves the conversation *on* the list, where deleting
  again finishes it.
- The other order fails to an invisible thread still holding a pin and a transcript.
- Both halves are rows of one sqlite file, so the usual failure takes both anyway.

**Deleting is not a turn.**

- No step, no trace, no graph run: nothing is being answered, so there is nothing to walk.
- The endpoint is shaped like forgetting a fact — `DELETE`, no body, `204`, and a store
  that went away is the 503 that shape already gives.

**The delete is confirmed over the page.**

- A fact can be told again, and a conversation cannot, so this one is asked about.
- The overlay is the shell the cited-source modal already uses: a dialog role, Escape
  and the backdrop as the ways out.
- What it says is what is lost *and* what is not: the documents and the memory stay,
  which is the thing a reader cannot see for themselves.
- Rejected: a gesture on the row — a delete nobody can make with a keyboard, and one
  careless flick from gone.
- Rejected: the browser's own `confirm` — it blocks the page, cannot be read by the
  page's own tests, and says nothing about what is lost.

**One delete control, drawn as an icon, in both rails.**

- A word per row repeated down a narrow rail reads as noise, and the two rails were
  already the same shape with two spellings.
- Drawn inline, as the rail's own toggle is: no dependency for one glyph.
- The accessible name is the row — the conversation, or the fact — not the verb, so a
  column of identical icons still says which is which.
- Nothing destructive is drawn in the palette's warm pair any more: the icon is quiet
  until it is reached for, and the button that confirms is a button like any other.

**The page follows the rule the list already has.**

- The row for the open conversation is disabled today, and the delete is disabled by the
  same reading, widened to the conversation cora is working in.
- The stow of a parked conversation is let go through the function that exists for it.
- The list is redrawn by the refresh every write on this page already goes through.

**What moves at the edges.**

- Ports: `conversations` and `graph` gain a method each; no port is added, so the map is
  unchanged.
- Guards: none, and no generated diagram — deleting walks no steps and adds no component.
- Docs: `README.md`, on a deleted conversation being gone from both stores.

## Risks / Trade-offs

- **A half-failed delete leaves a conversation the model has forgotten** → it stays
  listed, and deleting it again finishes the job.
- **A reader must leave a conversation to delete it** → the list is what they leave it
  through, and the alternative is deleting the page out from under them.
- **A turn running in a conversation blocks its delete** → briefly, and the alternative
  is a conversation that records itself back into the list.
- **Deleting is silent** → it is the reader's own row, said in one word, as forgetting a
  fact is.
