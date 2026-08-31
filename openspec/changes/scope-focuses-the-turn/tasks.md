Every item is one failing test, and group 2 comes first because every other group needs
the two new steps to exist. Ticked items are covered rather than counted: several items
are one test each, and a few share one.

Two items are recorded as covered elsewhere rather than written, and both are named where
they are ticked: the walk's recursion limit, which the graph adapter already sizes from
the sequence and has a test for, and the new trace kind's trip through a checkpoint,
which the allowlist guard covers by discovery.

## 1. The outer test

- [x] 1.1 **Outer.** Write a test that shows a fixture plugin's two fields loaded, one
      pinned mid-conversation, every later turn answered under it and the other field's
      tools never offered —
      `tests/acceptance/test_scopes.py::test_a_pinned_conversation_stays_in_its_field_and_reaches_nothing_else`

## 2. The walk gains *route* and *focus*

- [x] 2.1 Write a test that shows a turn's steps naming *screen*, *route*, *focus*, *work*
      and *answer*, in that order
- [x] 2.2 Write a test that shows the brief settled in *focus*, under the scope *route*
      named — the routed turn reads the routed field's persona
- [x] 2.3 Write a test that shows a refused question failing in *screen*, with no model
      call and so no scope read
- [x] 2.4 Covered: `recursion_limit_for` is sized from the walk, and its test walks the
      sizing exactly — the walk grew and that test still holds

## 3. The pin belongs to the conversation

- [x] 3.1 Write a test that shows a pin fixing the scope of every later turn on that thread
- [x] 3.2 Write a test that shows a pin surviving a checkpoint and read back off the thread
- [x] 3.3 Write a test that shows a second, different pin refused, naming the scope held
- [x] 3.4 Write a test that shows the same pin sent again accepted, changing nothing
- [x] 3.5 Write a test that shows turns taken before the pin unchanged when the thread reopens
- [x] 3.6 Write a test that shows the pin outranking the routed reading of the question

## 4. An unpinned turn is routed

- [x] 4.1 Write a test that shows a turn running under the scope a scripted model named
- [x] 4.2 Write a test that shows the next question on that thread routed afresh
- [x] 4.3 Write a test that shows one unpinned thread answering a turn in each scope
- [x] 4.4 Write a test that shows only the routed scope's tools offered to the model
- [x] 4.5 Write a test that shows a deployment offering one scope routing nothing

## 5. Ambiguity, and a question that fits no scope

- [x] 5.1 Write a test that shows an ambiguous question stopping the turn to ask which scope
- [x] 5.2 Write a test that shows the turn answering under the scope the user chose
- [x] 5.3 Write a test that shows a declined ambiguity answered in the default scope
- [x] 5.4 Write a test that shows a question fitting no scope answered with only the
      system-wide instructions and tools
- [x] 5.5 Dropped: a routing pause spends no round, because the routing call writes no
      assistant message — there is nothing a test could show that 5.2 does not

## 6. The trace says what the turn was focused on

- [x] 6.1 Write a test that shows the trace naming the scope and how it was settled
- [x] 6.2 Covered: the allowlist guard walks every `TraceStep` subclass, so the new kind
      is in the checkpoint by discovery rather than by anyone remembering

## 7. The travel plugin

- [x] 7.1 Write a test that shows the travel plugin registering instructions under its own
      scope, and nothing system-wide
- [x] 7.2 Write a test that shows the travel plugin registering no tool
- [x] 7.3 Write a test that shows a travel question answered from that plugin's own documents

## 8. What the deployment offers

- [x] 8.1 Write a test that shows `CORA_SCOPES` read as the scopes a turn may run under
- [x] 8.2 Write a test that shows a caller's own scopes winning over routing for one turn

## 9. The page

- [x] 9.1 Write a test that shows the ask endpoint carrying a pin and fixing the thread's scope
- [x] 9.2 Write a test that shows a session reporting the scope it is pinned to
- [x] 9.3 Write a test that shows the endpoint refusing a second, different pin as a sentence
- [x] 9.4 Write a test that shows the line naming the field arriving on the page's step
      stream, worded as the reader reads it
- [x] 9.5 Bring the component-map guard green again over the walk this change lengthens
- [x] 9.6 Bring the sequence-diagram guard green again over the two new steps

## 10. The router is measured

- [x] 10.1 Write a test that shows the recorded set carrying a scope per question, asked alone
      and as a follow-up
- [x] 10.2 Write a test that shows the report naming the share of scopes chosen rightly
- [x] 10.3 Write a test that shows a share under the recorded threshold failing the `llm` tier

## 11. What review found

- [x] 11.1 Write a test that shows the field the reader chose surviving the step being
      replayed — the reading now commits a step before the stop, so it is never redone
- [x] 11.2 Write a test that shows a refused question pinning the conversation to nothing
- [x] 11.3 Write a test that shows the page drawing the pin the thread holds rather than
      the one it sent, so a turn that failed after being admitted still closes the control
- [x] 11.4 Write a test that shows a scope's outline read as the paragraph its
      instructions open with, wrapped lines and `e.g.` included
- [x] 11.5 Write a test that shows the router told the names it may answer with and what
      each field is for, and nothing of the thread
- [x] 11.6 Write a test that shows a reply naming no offered field answered plainly, and
      one the model could not be asked about answered plainly too
- [x] 11.7 Write a test that shows the fixed field carrying a name a screen reader reads,
      rather than a label pointing at a control that is gone
- [x] 11.8 Write a test that shows a pin a refused turn asked for not waiting for the next
      turn to take it — found by the second review pass, in the first fix's own seam
- [x] 11.9 Write a test that shows a scope read that failed leaving the pin the page
      already knows about, rather than re-opening a control the engine has closed

## 12. The marker comes off

- [x] 12.1 Not used: the outer test was written green, after the walk it asserts. Recorded
      here rather than quietly ticked — the marker exists to keep CI green while a slice
      is in flight, and this slice was built in one pass
