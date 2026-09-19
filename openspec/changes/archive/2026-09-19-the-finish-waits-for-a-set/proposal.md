## Why

The button says "Save & finish" and can be pressed with nothing logged, which then has to be refused in words.

## What Changes

- The button reads "Finish"
- It is enabled only once a set has been logged, and goes quiet again when a new workout starts
- Capability `plugins` — what finishing an empty workout does changes

## Impact

- `plugins/fitness/src/cora/plugins/fitness/page/index.html` — the label, the state, and its style
- `plugins/fitness/tests/`, `frontends/react/ui/e2e/trainer.spec.ts` — the label and the state asserted
- `docs/what-ships-with-it.md` — the button's name
- Left alone: what a finish saves, the watch's finish, and cora
