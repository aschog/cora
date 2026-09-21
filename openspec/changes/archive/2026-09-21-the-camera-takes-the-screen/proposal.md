## Why

The camera is one frame among the controls, so the lifter films themselves in a window.

## What Changes

- While the camera shows, its picture fills the whole page
- The history and finish buttons, the exercise row, the sets and the weight are drawn over the picture
- The mirror and pose controls, the set count and the rest countdown keep their place between the row and the sets
- A clip still plays in the frame, as it does today
- With both rails folded, the picture is the whole screen, the folded rails under it, until the camera closes
- The trainer tells the shell when its camera has the view, and any page may say the same
- Capability `plugins` — what the trainer shows while the camera runs changes
- Capability `frontend` — a page that asks for the screen has it while both rails are folded

## Impact

- `plugins/fitness/src/cora/plugins/fitness/page/index.html` — the camera layer, its style, and two controls that move out of it
- `frontends/react/ui/e2e/camera.spec.ts` — the browser tier gains the one spec that runs with a camera
- `frontends/react/ui/src/App.tsx`, `App.module.css` — the frame over everything while a page asks and both rails are folded
- `frontends/react/ui/src/App.test.tsx` — the asking, drawn
- `docs/what-ships-with-it.md`, `docs/the-page.md`, `docs/how-to/write-a-plugin.md` — the screen, and what a page may ask the shell for
- Left alone: the plan, the sets, the finish, the save, the clip's frame, and cora
