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
- [x] **(ui)** the control is unavailable while the conversation is already new and empty —
      a click that changes nothing changes nothing
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
- [x] **(ui)** the control is reachable while it is unavailable: `disabled` takes a button
      out of the accessibility tree, and the rail's documents already settled that the
      reason has to be somewhere the reader can get at — prose beside the list there, read
      out here, where the header has no room for a sentence. Clicking it while there is
      nothing to start changes nothing

`NewSession` is inlined into `Header` — one call site, no logic of its own, and a comment
stating a rule enforced in `App`. `big-picture.md` no longer says the frontend keeps one
thread id per browser session.

#### Found by the branch review (`ai-code-reviewer`, second pass)

Every fix of the first pass killed its mutant. What was left was the promise the composer
note makes, one guard that had been half-applied, and the availability rule written twice.

- [x] **(ui)** a conversation load that lost the race says nothing about it either — the
      guard was on what a load *applies* and not on what it *reports*, so the failure of a
      load the reader walked away from followed them onto the new session
- [x] **(ui)** a question left running that fails says so: a failure is recorded nowhere,
      so the reader was told to wait under SESSIONS for an answer that had stopped
      existing. It stands until they ask their next question, which is them moving on
- [x] **(ui)** and nothing says a turn was asked elsewhere while it was asked here:
      `askingElsewhere={asking}` passed the whole suite, putting that sentence under every
      ordinary question
- [x] **(ui)** the control that is unavailable carries the reason, read out rather than
      drawn — the header has no room for the prose the document rail can afford, and
      `aria-disabled` announces a state, not a why

`start` is the one writer of the rule: `canStart` only draws it. The sessions list still
uses a real `disabled` for the conversation you are in, and settling `disabled` versus
`aria-disabled` for the whole page is not this story's to decide.

**Left as follow-up, deliberately.** A conversation load already in flight when a turn
lands on that thread applies a store snapshot taken before the turn: the page shows the
conversation without its newest answer until it is reopened again. Reproduced with no new
session involved — ask in A, reopen B, reopen A while that load is slow — so it is the
reconciliation between a landing turn and an in-flight load, not this story's control, and
it wants a story of its own rather than a review fix.

#### Found by the branch review (`ai-code-reviewer`, third pass)

The four fixes of the second pass each killed their mutant. What it found was one level
down in the same guard: the sentence the second pass added could be swallowed, and could
outlive what it was about.

- [x] **(ui)** a turn that fails while a reopen is loading is not swallowed by it — the
      failure was appended to the conversation on screen, and the load already on the wire
      replaced that conversation and took it with it. `here.current` says where the last
      load *put* the reader, not what they have asked for next, so a load still flying is
      the second half of the question
- [x] **(ui)** the failure of a question you left is not still said once you are back in
      the conversation it belongs to — the sentence names where the reader is, so it is
      false there, and it stood until the next question was asked

The page's two sentences are drawn from one place, in one order: a load that failed, and
then a question left running that will not be answered. The rule about there being
something to leave has one writer and one reader.

**Also left to the follow-up above.** `ask` re-reads the conversation when the store's own
list landed while its turn ran, and that read takes a ticket in the same race the reader's
clicks run in — so a reopen the reader asked for can lose to it and say nothing about
having lost. The guard is consistent (a load that lost the race says nothing); *why* a
reader's load can lose is the same counter that owes the follow-up its story.

#### Found by the branch review (`ai-code-reviewer`, fourth pass)

The third pass's `flying` counter was a guess at the question it was asked: *a load is on
the wire* is not *this conversation is about to be replaced* — a load that already lost its
race replaces nothing, and one that fails replaces nothing either. Routing on the guess
while drawing on the fact left a gap where the failure was said in neither place. The
counter is gone: the failure is recorded either way, and where it is said is one question,
asked once, when the page is drawn.

- [x] **(ui)** a turn that fails in the conversation on screen says so there, whatever
      else is loading
- [x] **(ui)** and it is not dragged onto a page it was never asked on — appending it
      regardless of where the reader is passed every test the pass had left
- [x] **(ui)** the page says both of its sentences at once, in one order, keyed by which
      sentence it is rather than by what it happens to say

The conversation is read in one place and reported from the read alone, so a failure inside
what the page does with the turns is not dressed up as the store being unreachable.

**Declined, with a reason.** The pass asked that being back in the failed turn's
conversation *clear* the sentence rather than suppress it, so leaving again does not raise
it a second time. It cannot: the reader is already in that conversation when the turn
fails, and clearing on arrival there is indistinguishable from clearing on the reopen that
swallowed the failure — which is the case the sentence exists for. It is cleared by the
next question, which is the reader moving on.

#### Found by the branch review (`ai-code-reviewer`, fifth pass)

Ten mutants of the fourth pass's work all died. What it found was the seam the rewrite of
`loaded` opened: reading and drawing fail differently, and only the read was still being
reported.

- [x] **(ui)** a conversation that cannot be drawn says so on the page — the read is
      awaited on its own, so a failure in what the page does with the turns escaped as an
      unhandled rejection and left a click that did nothing
- [x] **(ui)** and a turn that *succeeded* is not drawn as failed by the re-read that
      follows it: the internal message of that failure was reaching the reader where the
      answer belongs. The turn in hand is what lands when the re-read cannot be drawn —
      and only while the reader is still in the conversation, because a re-read is awaited
      and they can leave while it runs
- [x] **(ui)** both sentences are announced, not only drawn: one arrives with no click
      behind it, which is the same reason the header's unavailable control carries a reason
      a screen reader can reach

The flush that separates two arrivals in the race specs has a name that says what it waits
for.

**Declined, with a reason.** The pass asked that the lost-turn sentence retire once the
reader has seen the failure drawn in its own conversation, rather than standing until the
next question. Every rule available here is a guess at what the reader has read: the page
cannot tell a failure they read from one that was on screen for fifty milliseconds before a
load they had already asked for replaced it. Of the two errors, repeating a sentence about
an answer that died is the safer one, and the alternative — keeping the failed turn itself,
per thread, so that reopening that conversation finds it — is the page having a model for a
turn that exists nowhere but the page. That is the same missing model the two follow-ups
above want, and it belongs with them rather than in a review fix.

#### Found by the human review (`/code-review`, PR #37)

- [x] **(ui)** a conversation that cannot be drawn does not half-move the page into it:
      reopening changes the thread, the turns and the document read, and the turns are what
      can fail — so the reader sat in one conversation looking at another's, and their next
      question was asked on the thread they could not see. The turns are drawn first, and
      what cannot be drawn moves none of it
- [x] whether a load that could not be drawn is worth a sentence is the caller's to say: a
      reader who clicked a conversation is owed one, and a turn that re-read its own
      conversation has the answer in hand instead — the write inside the load was dead on
      that path, cleared by the refresh that follows every turn
