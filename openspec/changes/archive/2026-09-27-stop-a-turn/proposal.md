## Why

A turn that is taking minutes cannot be called off: the reader waits, and cora keeps
spending.

## What Changes

- The composer's ask control becomes a stop control while a turn runs, and pressing it ends that turn
- A stopped turn leaves the question on the page under a sentence saying the reader stopped it
- The reader who closes the tab stops the turn too, which today runs on unheard
- A turn ends at the next step or the next piece of prose, whichever comes first
- Capability `frontend` — three requirements for what the control does, what it leaves, and what it costs

## Impact

- `frontends/react/src/cora/frontends/react/api.py` — the streamed turn learns that nobody is reading it
- `frontends/react/ui/src/api.ts` — `ask` and `resume` take the signal of the turn they carry
- `frontends/react/ui/src/hooks/useTurn.ts` — holds the controller, and reads an abort as a stop
- `frontends/react/ui/src/components/Answer.tsx`, `App.tsx` — the control, and what raises it
- `frontends/react/tests/`, `frontends/react/ui/src/`, `frontends/react/ui/e2e/` — the tests of all four
- Left alone: `src/cora`, which gains no port, no step and no error — a stop is the frontend letting go
- Left alone: the Telegram bot, where there is no control to press mid-turn
