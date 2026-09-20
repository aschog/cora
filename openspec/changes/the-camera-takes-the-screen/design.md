## Context

The camera, a clip and the plan share one frame between the exercise row and the sets,
and that frame is all the camera fills. See proposal.md — Why.

## Goals / Non-Goals

**Goals** — a picture the size of the page, with every control still where the thumb
finds it.

**Non-Goals** — the clip, which stays in the frame. The browser's own fullscreen, which
an iPhone does not give a page and which would hide the shell on a laptop.

## Decisions

**The camera layer is pinned to the page's edges, and the frame stays in the flow.**

- The picture is drawn behind everything, and the frame keeps its band between the row
  and the sets.
- Whatever sits on the frame — the rest number, the set count, the mirror and pose
  controls — keeps its place with it.
- Rejected: pinning the frame itself, which puts every control on it under the rows
  unless each is offset by the rows' height.

**The controls over the picture take the rows' own tint.**

- A thin border on a moving picture is not a button, so each control gets the dark
  translucent ground the plan's rows already use.
- The exercise name gets the shadow the mirror label already wears over the picture.

**Two controls and the readout leave the camera layer for the frame.**

- The mirror switch, the pose button and the pose readout are the frame's, so pinning
  the camera does not carry them to the page's corners.
- They show only while the camera is the view, which the layer's own visibility gave
  them before.

**The page asks the shell for the screen, and the shell decides.**

- A frame cannot draw outside itself, so the shell is what can put it over the folded
  rails, and the page is what knows its camera has the view.
- One message either way, on cora's own origin, and the shell answers it only while both
  rails are folded: with a rail open, the rail is what the reader chose.
- Rejected: the browser's fullscreen from the page, which takes the display whatever the
  rails show, and which an iPhone does not give a page.
- Rejected: the shell reading the rails alone, which would bury their controls under a
  page that never asked.

**Closing the camera is the way back.**

- Over the whole screen the folded rails' controls are under the picture, and the camera
  button is over it.

**The clip keeps its frame.**

- A clip is watched between sets and the camera is worked through them, and only the
  second wants the whole screen.

## Risks / Trade-offs

- The picture is cropped to the page's shape, so its edges sit behind the rows → it is a
  mirror, and a lifter centres themselves in it.
- Before the stream is live the band shows cora's ground through the frame → that is
  the moment of the permission prompt and nothing longer.
- The browser tier grows a spec that needs a camera → chromium is given a fake one for
  that spec alone.
- A page that asks and never lets go keeps the screen → the shell forgets the asking
  when the page changes, and a page closing lets go as it goes.

## Ports, guards and diagrams

- No port, no guard, no diagram: the message is the first thing a page says to the shell,
  and `docs/how-to/write-a-plugin.md` writes it down.
- The plugin's own suite holds the hosts the page may reach, and none is added.
