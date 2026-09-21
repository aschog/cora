## Context

The camera, a clip and the plan share one frame between the exercise row and the sets,
and that frame is all the camera fills — see proposal.md, Why.

## Goals / Non-Goals

**Goals** — a picture the size of the page, with every control still where the thumb
finds it.

**Non-Goals** — the clip, which stays in the frame. The browser's own fullscreen, which
an iPhone does not give a page and which would hide the shell on a laptop.

## Decisions

**The picture's stage is pinned to the page's edges, and the frame stays in the flow.**

- Once there is a picture its stage is painted under everything, and the frame keeps its
  band between the row and the sets, its ground kept until the picture arrives.
- Whatever sits on the frame — the rest number, the set count, the mirror and pose
  controls — keeps its place with it.
- Rejected: pinning the frame itself, which puts every control on it under the rows
  unless each is offset by the rows' height.

**The controls over the picture take the rows' own tint.**

- A thin border on a moving picture is not a button, so each control gets the dark
  translucent ground the plan's rows already use.
- The exercise name gets the shadow the mirror label already wears over the picture.

**The controls and the readout stay beside the stage, not in it.**

- The mirror switch, the pose button and the pose readout keep the frame's band, and the
  camera layer's own visibility still hides them with it.

**The page asks the shell for the screen, and the shell decides.**

- A frame cannot draw outside itself, so the shell is what can put it over the folded
  rails, and the page is what knows its camera has the view.
- One message either way, checked against cora's own origin on receipt, and the shell
  answers it only while both rails are folded: with a rail open, the rail is what the
  reader chose.
- The shell answers by not drawing what is left of the folded rails, so the frame has the
  screen while the shell's own notices keep the top.
- Rejected: lifting the frame over everything, which buries a notice the reader must see.
- Rejected: the browser's fullscreen from the page, which takes the display whatever the
  rails show, and which an iPhone does not give a page.
- Rejected: the shell reading the rails alone, which would bury their controls under a
  page that never asked.

**Closing the camera is the way back, and the camera closes itself when the picture goes.**

- Over the whole screen the folded rails' controls are not drawn, and the camera button
  is over the picture.
- A picture taken away underneath — another app, a sleeping tab — closes the camera, so the
  page lets go without a hand on it.
- The asking is read against the page it came from, and a page that changes takes it
  with it.
- The page asks once the picture is there, not when the browser starts asking for it, so
  the shell moves once and never for an empty frame.
- One asking of the browser at a time: a late answer to an earlier one is stopped, not
  shown.

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
- A page that asks and never lets go keeps the screen → the asking is tied to the page, a
  page closing lets go as it goes, and a picture ending closes the camera.
- The shell sat 8px in from every edge on the browser's own body margin → it is reset, so
  the whole screen is the whole screen.

## Ports, guards and diagrams

- No port, no guard, no diagram: the message is the first thing a page says to the shell,
  and `docs/how-to/write-a-plugin.md` writes it down.
- The plugin's own suite holds the hosts the page may reach, and none is added.
