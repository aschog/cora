## Why

The conversation sits under the panels as a third thing in the rail, so it is narrow,
it is always there, and the list of other conversations is nowhere near it.

## What Changes

- The conversation moves inside the sessions panel and takes the whole rail
- Opening a conversation from the list makes the rail that conversation's chat
- A way back to the list stands over it, so another conversation is two clicks away
- The chat is headed by what opened the conversation, its field and how long it is
- Only a conversation fixed to a field with a page is chatted in the rail at all
- Every such conversation is marked in the list, so it is told apart at a glance
- A turn asked in the rail no longer moves the panels to the steps, which would hide it
- Capability `frontend` — the rail's second slot becomes the sessions panel's two states

## Impact

- `frontends/react/ui/src/components/SessionsPanel.tsx` — the list, its marks and the chat
- `frontends/react/ui/src/App.tsx` — the rail's slot goes, the panel takes what it held
- `frontends/react/ui/src/App.module.css` — the share between panel and chat is now one thing
- `frontends/react/ui/src/hooks/useTurn.ts` — the panels stay put while the rail is a chat
- `frontends/react/src/cora/frontends/react/api.py` — a listed conversation says what it is pinned to
- `frontends/react/ui/src/api.ts` — the pin on a session, and the page a field has
- `docs/the-page.md` — where a conversation is drawn beside a page
- Left alone: the centre, which holds the page exactly as it does now
- Left alone: the pin itself, and every other panel
- Not here: when a conversation was last spoken to, which nothing stores
