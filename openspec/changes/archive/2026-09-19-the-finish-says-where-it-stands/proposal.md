## Why

A save that went through puts a green strip over the trainer, and the button says nothing of where the workout stands.

## What Changes

- The finish button reads where it stands: no sets logged yet, finish, or saved until the next set is logged
- A save cora took says nothing on the strip, unless the watch ended the workout, when the strip says so
- A save cora refused still says so on the strip, as it did
- Capability `plugins` — what a finished workout shows changes

## Impact

- `plugins/fitness/src/cora/plugins/fitness/page/index.html` — the button's three faces, and the success line
- `plugins/fitness/tests/`, `frontends/react/ui/e2e/trainer.spec.ts`, `frontends/react/ui/e2e/watch.spec.ts` — the button read, not the strip
- `docs/what-ships-with-it.md` — the button described
- Left alone: the refusals, the clipboard fallback, and cora
