## Why

A part of the page that fails to draw unmounts all of it, leaving a blank window and no
explanation.

## What Changes

- A column that throws while drawing is replaced by a sentence, not by nothing
- The other two columns are still drawn, so the conversation survives a broken rail
- A panel that broke is left behind by moving to another one, the strip staying usable
- Trying again re-draws what threw, so a panel is not broken until the page is reloaded
- Whatever threw reaches the console, which is the only record of it
- The page under everything catches what falls outside a column
- Capability `frontend` gains what the screen does when part of it cannot be drawn

## Impact

- `frontends/react/ui/src/components/ErrorBoundary.tsx` — new, the one thing hooks cannot do
- `frontends/react/ui/src/App.tsx` — one around each column, the panels keyed on the tab
- `frontends/react/ui/src/main.tsx` — one under all three, for what falls outside them
- `frontends/react/ui/src/styles.css` — what the sentence and its control are drawn as
- Left alone: every panel and rail, which say nothing about failing to draw
- Left alone: the banners, which are about a request that failed rather than the page
- Left alone: the API, which cannot tell whether what it answered could be drawn
