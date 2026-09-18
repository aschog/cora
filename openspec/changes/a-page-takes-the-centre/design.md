## Context

`a-plugin-brings-a-page` serves a field's page and says on the fields listing where it
is. Nothing draws it. See proposal.md — Why.

## Goals / Non-Goals

**Goals** — the page in the middle when the conversation is fixed to its field, the
conversation beside it and always reachable, and today's screen everywhere else.

**Non-Goals** — a narrow layout, which this shell has never had. A page taking part in a
turn. Talking to the page, or it to the shell — it has cora's API and needs no second
channel. Containing what the page may do, settled in the previous change.

## Decisions

**A fixed field decides, which is the pin or the only field there is.**

- `field` is `pin ?? answered ?? home`, so keying on it would turn the screen into a
  trainer because a turn happened to be routed there — a layout nobody asked for.
- One field loaded is one routing cannot choose against, so every conversation is already
  fixed to it and no picker is drawn to fix it with — the rail says as much where it
  works out where it sits, and the page reads the same clause rather than a new one.
- That case is the first deployment of this feature, not an edge of it: one plugin
  dropped in, no fields configured.

**The conversation is a second slot in the rail, not a fifth panel.**

- The tabs key their boundary on the tab, and a turn moves them to the steps, so a
  conversation drawn inside that is unmounted by the reader's own question — losing the
  draft, the scroll and the answer arriving.
- It keeps a boundary of its own, because the rule that a part which cannot be drawn
  becomes a sentence is about where a thing is drawn, not about which column it started in.
- Rejected: suppressing the move to the steps while a page is up — it would trade the
  trace, which is the thing worth watching while a tool runs.

**The rail becomes a column of two, and each half scrolls itself.**

- Dropped into a block box the conversation cannot scroll at all: its scroller claims free
  space there is none of, so the rail scrolls instead and the composer rides away with it.
- The panel takes what it needs and the conversation takes the rest, so neither a long
  list nor a long answer can push the composer out of the box.
- The composer's own inset was measured for a column twice the rail's width, so the rail
  gives it one of its own rather than moving the number both columns read.

**The middle is one slot with two things it can hold.**

- The page or the conversation, each in the boundary the middle already has, so a page
  that cannot be drawn is the sentence that column already knows how to say.
- A frame that fails to load throws nothing, so nothing catches it: the reader sees the
  plugin's own blank, and that is the plugin's to answer for.
- A page goes when its plugin does, and the reader's confirmation is what has to put the
  conversation back — the listing it is read from is mended in the same act.

**Folding the rail is how a page gets the screen.**

- A camera page wants width, and the fold already exists — it is not a second control.

**The landmark is the slot, not what sits in it.**

- Whatever the middle holds is wrapped in the one main region, so the conversation stops
  being one and needs no say in where it is drawn.
- A frame cannot be that region itself, so the wrapper is needed either way.

**The conversation names itself from what it holds.**

- The question that opened it is its own first turn, so the heading is read off what is
  already there rather than passed in.

## Risks / Trade-offs

- The reader loses the conversation's width: it is drawn in a rail sized for panels, and a
  long answer reads narrower than it does in the middle.
- Folding the rail unmounts the conversation, so a question typed and not yet asked is
  gone when it comes back — the cost of one rail holding both.
- Two places now draw the conversation, so a change to it has two layouts to hold.
- The page is same-origin with the shell, so it shares the browser storage the shell
  parks a draft in, and may reach the shell's own document — the trust the previous
  change wrote down, now with a frame around it.

## Ports, guards and diagrams

- No Python, no port and no new API: the previous change put everything the shell reads
  on the fields listing.
- The style guard holds a class against the module that draws it and not across two, so
  what the rail changes about the conversation is declared where the conversation is.
- The browser tier gains a plugin of its own bringing a page, rather than lending one to
  the fixture three specs already pin, and the store it is laid out in copies directories.
