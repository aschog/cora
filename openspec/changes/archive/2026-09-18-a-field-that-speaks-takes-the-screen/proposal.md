## Why

Training starts on the wrist, but the screen stays wherever it was left, so the trainer
the workout is being logged into has to be found by hand.

## What Changes

- The shell asks every field that has a page for its notice, every few seconds
- A notice newer than the last one it saw opens that field's newest conversation
- Nothing is read out of the notice: a field that speaks takes the screen, whatever it said
- A field with no conversation of its own takes nothing, there being none to open
- A notice that opens the conversation already on the page moves nothing
- The notice standing when the page loads is not acted on, only one written after it
- Capability `frontend` gains what a written notice does to the screen
- Not here: what a notice means, which is the writing page's business and the reading one's

## Impact

- `frontends/react/ui/src/hooks/useNotices.ts` — the poll and what it opens
- `frontends/react/ui/src/App.tsx` — the hook wired to the conversation the page shows
- `frontends/react/ui/src/api.ts` — the notice read, as every other read is declared
- `frontends/react/ui/e2e/watch.spec.ts` — the browser tier: a notice takes the screen
- Left alone: the notice itself and the trainer, both of which this only watches
- Left alone: the pin, which only a turn writes, so a field with no conversation waits
- Left alone: every field with no page, which is asked nothing
