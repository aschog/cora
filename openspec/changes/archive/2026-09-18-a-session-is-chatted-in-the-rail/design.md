## Context

`a-page-takes-the-centre` put the conversation in the rail as a slot under the panels.
It is narrow, it is always there, and the list of other conversations sits above it
rather than behind it. See proposal.md — Why.

## Goals / Non-Goals

**Goals** — the sessions panel with two states, the whole rail for whichever it is
showing, and a conversation that belongs to a field with a page told apart in the list.

**Non-Goals** — the centre, which keeps the page. When a conversation was last spoken
to, which nothing stores. A conversation of a field with no page moving anywhere.

## Decisions

**The rail's second slot becomes the sessions panel's second state.**

- One thing in the rail under the tabs, not two sharing it, so the share between them
  stops being a number anybody has to pick.
- The list and the chat are the same subject — which conversation — so the panel that
  lists them is the panel that holds one open.

**The panels stay where they are while the rail is a chat.**

- A turn moving them to the steps would take the conversation off the screen at the
  moment the reader is watching for an answer, which is the whole of why it is there.
- The trace is one tab away and stays that way, so what is traded is a jump nobody asked
  for rather than the trace itself.

**Only a conversation fixed to a field with a page is chatted here.**

- The rail is beside that page: a conversation about something else drawn there would be
  a second place the reader has to look for the conversation they are in.
- So the middle keeps it in every other case, exactly as before this change.

**A listed conversation says what it is pinned to, and the page says what that means.**

- The mark is drawn from the pin the conversation holds rather than from the fields its
  turns happened to be answered in — the first is a decision, the second is a reading.
- Read per listed conversation at the moment the list is asked for, because a pin lives
  in the conversation's own state and nothing else records it.

**The head of the chat is read off what is already there.**

- The question that opened it, the field it is fixed to, and how many turns it holds are
  all on the page already, so the head costs no read of its own.
- When it was last spoken to is not: nothing records a time, and a store that did is a
  change of its own.

## Risks / Trade-offs

- Listing the conversations now reads each one's pin, which is a read per row — fine for
  the handful a person keeps, and the first thing to store if it ever is not.
- Moving between tabs unmounts the chat, so a question typed and not asked is lost on the
  way to the steps and back.
- A conversation with a great many turns is drawn in a rail sized for panels, which is
  narrower than the middle it used to have.

## Ports, guards and diagrams

- No port and no core change: the pin is already readable per conversation.
- The style guard holds the panel's own classes, as it holds the rest.
- The browser tier covers the two states and the way between them.
