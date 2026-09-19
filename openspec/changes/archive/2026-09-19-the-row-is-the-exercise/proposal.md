## Why

Each exercise row carries a sets count and the weight, which the lifter does not want to read there.

## What Changes

- An exercise's row carries its number and its name, and no count or weight
- Progress reads off the set buttons of the current exercise, as it already does
- Capability `plugins` — what a row shows changes

## Impact

- `plugins/fitness/src/cora/plugins/fitness/page/index.html` — the readout and its style go
- `plugins/fitness/tests/`, `frontends/react/ui/e2e/trainer.spec.ts` — progress asserted off the sets
- Left alone: the sets panel, the finish, the save, and cora
