## Why

The camera is one frame among the controls, so the lifter films themselves in a window.

## What Changes

- While the camera shows, its picture fills the whole page
- The history and finish buttons, the exercise row, the sets and the weight are drawn over the picture
- The mirror and pose controls, the set count and the rest countdown keep their place between the row and the sets
- A clip still plays in the frame, as it does today
- Capability `plugins` — what the trainer shows while the camera runs changes

## Impact

- `plugins/fitness/src/cora/plugins/fitness/page/index.html` — the camera layer, its style, and two controls that move out of it
- `frontends/react/ui/e2e/camera.spec.ts` — the browser tier gains the one spec that runs with a camera
- `docs/what-ships-with-it.md` — the camera takes the page while it runs
- Left alone: the plan, the sets, the finish, the save, the clip's frame, and cora
