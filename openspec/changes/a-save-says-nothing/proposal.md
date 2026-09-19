## Why

A save that went through puts a green strip over the trainer, which the lifter does not want to read.

## What Changes

- A save cora took says nothing on the strip, unless the watch ended the workout, when the strip says so
- A save cora refused still says so, as it did
- Capability `plugins` — what a finished workout shows changes

## Impact

- `plugins/fitness/src/cora/plugins/fitness/page/index.html` — the success line
- `plugins/fitness/tests/`, `frontends/react/ui/e2e/trainer.spec.ts`, `frontends/react/ui/e2e/watch.spec.ts` — the save seen in the field, not on the strip
- Left alone: the refusals, the clipboard fallback, and cora
