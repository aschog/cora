## Why

Every conversation has the same address, so none can be linked to, reloaded into, or
left by pressing back.

## What Changes

- The conversation on screen is named in the address, and opening one writes it there
- A page opened at an address opens in the conversation it names
- The address changing under the page — back, or a pasted link — opens that conversation
- A conversation the reader started is named once it has answered, not before
- Starting over takes the conversation out of the address, having nothing to name yet
- A card left open still outranks the address, being reachable by nothing else
- An address naming anything that could mean another path names no conversation
- Capability `sessions` gains the address a conversation is reached by

## Impact

- `frontends/react/ui/src/route.ts` — new, where a conversation is read out of the address and written into it
- `frontends/react/ui/src/hooks/useHash.ts` — new, the address subscribed to rather than mirrored
- `frontends/react/ui/src/hooks/useConversation.ts` — the page opens where the address or the stow says
- `frontends/react/ui/src/App.tsx` — writes the address on opening, follows it when it changes
- `frontends/react/ui/src/api.ts` — every thread reaching a path is escaped on the way in
- `docs/how-to/run-the-react-shell.md` — what the address holds and why it is the hash
- Left alone: the API, which knows nothing of how a page addresses what it asks for
- Left alone: the stow, which remains the only route back to an unlisted card
