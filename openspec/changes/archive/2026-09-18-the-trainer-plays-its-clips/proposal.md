## Why

A clip in the trainer is a link out of the page, so a lifter mid-set is sent to another
tab to watch the movement they opened the trainer to see.

## What Changes

- A clip plays in the frame the plan and the camera already share
- It starts where the plan says it starts, muted, so the browser will begin it
- It is asked of the host that sets no cookie until a clip is played
- The map the old build inlined clips into goes: nothing fills it, and nothing can
- Capability `plugins` — what the fitness page reaches, one host for another

## Impact

- `plugins/fitness/src/cora/plugins/fitness/page/index.html` — the player, and the dead map
- `plugins/fitness/tests/fitness/test_plugin.py` — the host named, the old one gone
- `frontends/react/ui/e2e/trainer.spec.ts` — a clip opened is a clip playing
- `docs/privacy-and-ethics.md`, `docs/what-ships-with-it.md` — where a clip comes from
- Left alone: the thumbnails, which already come from the service they came from
- Left alone: the camera and the pose overlay, which share the frame as they did
