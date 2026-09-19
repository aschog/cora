## Why

The camera watches the lifter and the pose overlay reads their joints, but nobody is counting.

## What Changes

- With the pose overlay on, the trainer counts reps from the landmarks and shows the running count over the frame
- The count is a readout: it never writes a set's reps, and the set is still logged by hand
- One counter serves every exercise the hands move against the torso, or the torso against planted hands, so no exercise names itself in the code
- The count starts again at nought when a set is logged or the exercise changes
- Capability `plugins` — what the trainer does with the camera changes

## Impact

- `plugins/fitness/src/cora/plugins/fitness/page/index.html` — the counter, the readout over the frame, and its style
- `frontends/react/ui/e2e/trainer.spec.ts` — the counter driven from a written sequence of landmarks, in the tier that runs the page
- Left alone: the pose overlay itself, the set boxes, the rest timer, the finish, the save, and cora
