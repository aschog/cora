## Why

A field may bring a page, and the shell has nowhere to draw one, so the only way to
reach it is to type its address.

## What Changes

- A conversation fixed to a field with a page is worked in that page, which takes the centre
- A deployment offering one field is fixed to it already, so its page is drawn unpinned
- The conversation moves into the right rail, under the panels and above its own composer
- It sits outside the panel that the tabs switch, so asking never takes it off the screen
- The conversation there is headed by the question that opened it, under the sessions listed above
- Folding the right rail gives the page the whole width, and unfolding brings the talk back
- A field with no page draws today's page, unchanged, and so does an unpinned conversation
- The page is framed with the camera allowed and nothing sandboxed away, as its trust says
- A page whose plugin has gone leaves the centre to the conversation again
- Capability `frontend` gains what the screen does when a field has a page

## Impact

- `frontends/react/ui/src/hooks/useRails.ts` — the pinned field's page, derived beside it
- `frontends/react/ui/src/api.ts` — the fields listing carries a page per field
- `frontends/react/ui/src/App.tsx` — the centre branches, and the rail holds the talk
- `frontends/react/ui/src/components/Answer.tsx` — drawn in a rail as well as in a column
- `frontends/react/ui/src/App.module.css`, `Answer.module.css` — the frame and the rail's column
- `frontends/react/ui/e2e/`, `Makefile` — a browser tier over a fixture plugin with a page
- `docs/the-page.md` — where a plugin's page is drawn, and what folds
- Left alone: the pin, which decides the field and is not changed to decide a layout
- Left alone: every panel, which keeps its tab, its boundary and its contents
- Left alone: cora's API, which change `a-plugin-brings-a-page` already widened
