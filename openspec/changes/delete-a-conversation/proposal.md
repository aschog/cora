## Why

A conversation the reader is finished with cannot be got rid of, so the list only ever
grows.

## What Changes

- A conversation in the sessions list can be deleted, from the list itself
- Deleting reaches both halves of it: the turns recorded, and the thread's own state
- So the pin, the model's transcript and any turn parked mid-question go with it
- One call drops both, because a caller that can drop one half leaves a conversation
  half-there
- The conversation being read is not deletable, so the page is never deleted out from
  under the reader
- A page holding a card for that conversation forgets it, so no reload returns to it
- Deleting a conversation no store holds is already done rather than refused
- New capability `sessions`, which nothing before this change describes

## Impact

- `src/cora/ports/conversations.py`, `src/cora/ports/graph.py` — each gains a way to drop one thread
- `src/cora/adapters/sqlite_conversations.py` — the turns of one thread are deleted
- `src/cora/adapters/langgraph_runner.py` — over the checkpointer's own `delete_thread`
- `src/cora/engine/agent.py` — the one call that drops both halves
- `frontends/react/src/cora/frontends/react/api.py` — `DELETE /api/sessions/{thread_id}`
- `frontends/react/ui/src/` — the icon, the question it raises, the request behind it, and the stow it clears
- `frontends/react/ui/src/components/MemoryPanel.tsx` — the same row and the same control
- `README.md` — that a deleted conversation is gone from both stores
- Left alone: what the list holds and how a conversation is reopened, neither of which changes
- Left alone: memory and documents, which belong to the user and the field, not the thread
- Left alone: deleting every conversation at once, which no story asks for
- Left alone: what the list says about each conversation, which is its own story
