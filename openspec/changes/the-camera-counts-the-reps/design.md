## Context

The page already runs MediaPipe's pose landmarker per frame and draws the skeleton, and
its readout reports how sure the model is about each joint pair. Nothing reads the
landmarks for anything else, and the plan is an arbitrary sheet of exercises, so no code
here may name one.

## Goals / Non-Goals

**Goals:**

- One counter for every exercise in the plan, from swings to push-ups to the halo.
- A pure function over a sequence of landmark frames, callable from the browser tier.
- A readout that reads like the rest timer, because it sits in the same place.

**Non-Goals:**

- Judging form, depth or tempo — the count says how many, never how well.
- Writing the count into a set, or logging a set when it reaches the target.
- Telling one exercise from another, or reading the plan at all.

## Decisions

- **The signal is the dominant coordinate, chosen per frame.** Every rep here is a cycle,
  but each moves a different part: the wrists for a snatch, the shoulders for a push-up,
  the hips for a deadlift. So the counter tracks a handful of points, and each frame
  takes whichever coordinate swung widest over the window. A fixed wrist-height rule was
  the alternative, and it counts roughly half the plan.
- **The frame of reference is the torso.** Points are measured from the centre of the
  torso box and divided by its length, so distance from the camera and walking about
  drop out. Raw image coordinates were the alternative, and they count a step as a rep.
- **The trigger is a Schmitt trigger calibrated from the window.** Thresholds sit inside
  the window's own swing, so nothing is tuned per exercise. A fixed threshold was the
  alternative, and it needs a number per movement.
- **Two gates keep noise out.** A swing under a fraction of torso length does not count,
  and neither does one inside a minimum period. This is what stands between the counter
  and a lifter shifting their feet.
- **The readout is a twin of the rest timer**, sharing its markup and its `.num` rule,
  shown when the overlay is on and no rest is running. The two never show together.
- **The counter is exposed on `window`,** as `sessionText` already is. The page stays one
  file, and the browser tier calls the function the browser actually loaded.

## Risks / Trade-offs

- Rhythmic movement that is not a rep counts → the amplitude and period gates narrow it,
  they do not close it, and a `ponytail:` comment says so.
- The dominant coordinate can flip mid-set → the points move together on a two-armed
  lift, so a flip between them does not change the count.
- A rep slower than the window looks like drift → the window is sized for the slowest
  movement in the plan, and a slower one undercounts.
- The model runs lite and can lose a joint → a frame with no pose is skipped, not
  counted as a turning point.

## Ports, guards and diagrams

None. The change is inside the plugin's page, and touches no port, no guard and no
generated diagram.
