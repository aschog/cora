## Context

The tool this page came from inlined every clip into a built copy of itself, and the
tracked page it was ported from carries an empty map and a link out. See proposal.md.

## Goals / Non-Goals

**Goals** — the clip playing in the frame, from the moment the plan names.

**Non-Goals** — clips that play with no network, which is the build step this page was
deliberately ported without. Sound, which a browser will not start unasked.

## Decisions

**The clip is embedded rather than downloaded.**

- The page already reaches the service for its thumbnails, and a clip is the same
  material from the same place.
- Rejected: porting the inlining build — it wants two binaries on the machine, bakes
  tens of megabytes into a file a wheel would carry, and answers a problem this
  deployment does not have.

**From the host that sets no cookie until a clip is played.**

- The reader opened a trainer, not a session with a video service.

**The map nothing fills goes with it.**

- A branch whose first arm can never be taken is a branch that reads as a choice.

## Risks / Trade-offs

- A clip needs a network, and a gym without one has the plan, the sets and the camera
  but no clip — which the frame shows as the service's own empty player.
- A video whose owner disallows embedding plays as that service's refusal in the frame,
  where before it was a link that would have worked.

## Ports, guards and diagrams

- No port, no core change: the page is the plugin's, and this is inside it.
- The plugin's own suite holds the hosts the page may reach, and this swaps one.
