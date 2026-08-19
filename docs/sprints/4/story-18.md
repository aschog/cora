# Story 18: A conversation you can leave

**As a** reader · **I want** to start a new session · **So that** a fresh line of
questioning does not inherit the conversation I was just in

> **Given** a conversation with turns in it
> **When** I start a new session
> **Then** the page is empty, the next question runs on a new thread, and the
> conversation I left is listed under SESSIONS to reopen

The header already folds both rails; starting over belongs beside them, because it is the
same kind of control — what the page *is showing*, not what cora is being asked. The
button sits at the right end, before the right rail's toggle.

Nothing is added server-side: a thread exists once a turn is recorded on it, so a new
session is a thread id the page has not used and an empty conversation under it.

**A turn in flight stays with the conversation it was asked in.** `here.current` and the
thread on `live` already mean that; leaving mid-turn is the reopen case with no load
behind it. Asserted rather than built.

## Test list

**Tier:** **(ui)** vitest, run by `npm test` in `frontends/react/ui`.

- [x] **(ui)** the header offers a way to start a new session
- [x] **(ui)** starting one takes the conversation off the page
- [x] **(ui)** the question asked next runs on a thread other than the one before it
- [x] **(ui)** the control is disabled while the conversation is already new and empty —
      a click that changes nothing is not offered
- [x] **(ui)** the plan panel is empty afterwards: the steps of the turn left behind
      speak for a conversation that is no longer on screen
- [x] **(ui)** and the source panel with it — the document the answer opened is not this
      conversation's to mark, as leaving one by reopening another already knew
- [x] **(ui)** an answer arriving after a new session started does not land on it
- [x] **(ui)** the conversation left behind is listed under SESSIONS
