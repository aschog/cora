## Context

A Zepp OS workout extension is a screen the watch's own workout app creates and destroys;
a probe on the wrist proved what it can and cannot say. See proposal.md.

## Goals / Non-Goals

**Goals** — the workout starts on the page when it starts on the wrist, and is saved from
the wrist when the lifter is done.

**Non-Goals** — the pulse, which the lifter does not want logged. Ending the system
workout from the page, which Zepp OS offers no call for. Working without a network.

## Decisions

**The end of a workout is a tap, not an event.**

- A probe posting from every lifecycle point over five workouts was heard at `onInit` and
  `onPause` and never once at `onDestroy`: the screen is torn down without the write
  reaching the phone.
- `onPause` cannot stand in — it fires identically on every swipe away from the screen.
- So the lifter taps, and the tap is the one thing the design buys back: a workout
  extension supports click events on its widgets, where gestures and the side button are
  refused.
- Rejected: guessing the end from a silence after the last `onPause`, which would save a
  workout every time the lifter looked at another screen and left it.

**The screen writes the field's notice directly.**

- The extension has the phone's network through the messaging bridge, and a notice is a
  small object written under a field's name — which is all this needs.
- Rejected: a listener of its own, as the tool this came from had — a second process to
  start, with cora already serving on the same machine.

**The page is the memory.**

- A notice is replaced whole, so the start is gone once the finish is written, and the
  page keeps what it has read.
- A page opened after the workout ended sees only the finish, and finishes on the start
  it knew — which is what it does today with no watch at all.

**The pulse goes rather than being left unfed.**

- Nothing writes it once the sensor is dropped, and a heart line reading a dash is worse
  than no heart line.

## Risks / Trade-offs

- A tap by accident saves the workout and starts a fresh one; a tap before any set is
  logged saves nothing, and the page's own history keeps whatever was saved.
- The phone must reach cora, so cora binds past loopback and the whole API is on the
  network with it — `CORA_HOST` is where a deployment decides that.
- The extension's source is checked in but built and installed by hand against real
  hardware, so its own suite can only hold what the source says, not what the wrist does.
- Zepp keeps its record of the workout whatever the page does, so the two are separate
  accounts of one session.

## Ports, guards and diagrams

- No port and no core change: the page and the watch app are both the plugin's own.
- The plugin's suite already holds every host the page may reach, and this adds none.
- No diagram changes: none of the six draws a plugin's page or what talks to it.
