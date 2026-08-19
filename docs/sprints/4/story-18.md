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

#### Found by the branch review (`ai-code-reviewer`, PR #37)

Every ticked item killed its mutant. What the pass found was the state around the button:
one writer that did not join a race the page already runs, and a mid-turn start that left
a page nobody could use and nothing on it to say why.

- [x] **(ui)** a reopen still loading when a new session starts does not land on it —
      `start` changed which conversation the page was in without claiming `loads`, so a
      slow reopen resolved on top of it and put the reader back in the conversation they
      had just left, on its thread
- [x] **(ui)** a turn left running says so where the question would be typed: cora answers
      one question at a time, and with the question, the plan and the banner all belonging
      to the conversation left behind there was nothing on the page to explain a composer
      that could not be typed in
- [x] **(ui)** and the answer lands in the conversation it was asked in, reopenable from
      SESSIONS — the story claimed nothing is thrown away and asserted only that the
      answer stays off the new page
- [x] **(ui)** a banner raised by the conversation left behind does not follow the new
      session
- [ ] **(ui)** the control is reachable while it is unavailable: `disabled` takes a button
      out of the accessibility tree, which this page settled once already for the rail's
      documents, and clicking it while there is nothing to start changes nothing

`NewSession` is inlined into `Header` — one call site, no logic of its own, and a comment
stating a rule enforced in `App`. `big-picture.md` no longer says the frontend keeps one
thread id per browser session.
