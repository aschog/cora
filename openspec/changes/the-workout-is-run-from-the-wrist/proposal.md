## Why

The watch already runs the training and the page already logs it, but neither knows the
other, so every workout is started and saved on the page by hand.

## What Changes

- The fitness plugin brings a Zepp OS workout extension: one screen inside the workout
- That screen shows the workout's running time, so the lifter sees the link is up
- It writes the fitness field's notice when it opens, and again when its control is tapped
- The trainer page follows that notice, a start newer than its workout becoming the start
- A tap the page has not acted on finishes the workout and uploads it, without asking
- A tap with no set logged saves nothing, and both the page and the wrist say so
- The screen says whether cora took what it wrote, so a dead link is seen on the wrist
- The pulse the port carried over goes: no sensor, no permission, no heart line
- A command bakes cora's address into the app and hands it to the Zepp tooling
- Capability `plugins` gains what the fitness field's watch does
- Not here: ending the workout from the page, which Zepp OS offers no call for
- Not here: the notice itself, which the change before this brings

## Impact

- `plugins/fitness/watch/` — the extension's source, outside `src` so no wheel carries it
- `plugins/fitness/src/cora/plugins/fitness/page/index.html` — the notice followed, the pulse gone
- `plugins/fitness/tests/fitness/test_plugin.py` — where the page reaches, and what the watch writes
- `frontends/react/ui/e2e/` — the browser tier: a notice written, a workout saved
- `Makefile` — one target that bakes the address and builds the app
- `docs/how-to/get-started.md` — putting the watch on, and what it needs to reach cora
- Left alone: the notice route, which this change only writes to and reads
- Left alone: cora's core, the turn and every other plugin
- Left alone: Zepp's own record of the workout, which is untouched either way
