Every item is one failing test, and group 2 comes first because every other group needs
the two new steps to exist. Ticked items are covered rather than counted: some items are
one test each, and a few share one.

## 1. The outer test

- [ ] 1.1 **Outer.** Write a test that shows two scopes loaded, one pinned mid-conversation,
      every later turn answered under it and the other scope's tools never offered. Mark it
      `@pytest.mark.xfail(strict=True)`

## 2. The walk gains *route* and *focus*

- [ ] 2.1 Write a test that shows a turn's steps naming *screen*, *route*, *focus*, *work*
      and *answer*, in that order
- [ ] 2.2 Write a test that shows the brief settled in *focus*, under the scope *route* named
- [ ] 2.3 Write a test that shows a refused question failing in *screen*, with no scope read
- [ ] 2.4 Write a test that shows a five-step walk completing inside the recursion limit the
      graph sizes for it

## 3. The pin belongs to the conversation

- [ ] 3.1 Write a test that shows a pin fixing the scope of every later turn on that thread
- [ ] 3.2 Write a test that shows a pin surviving a checkpoint and read back off the thread
- [ ] 3.3 Write a test that shows a second, different pin refused, naming the scope held
- [ ] 3.4 Write a test that shows the same pin sent again accepted, changing nothing
- [ ] 3.5 Write a test that shows turns taken before the pin unchanged when the thread reopens
- [ ] 3.6 Write a test that shows the pin outranking the routed reading of the question

## 4. An unpinned turn is routed

- [ ] 4.1 Write a test that shows a turn running under the scope a scripted model named
- [ ] 4.2 Write a test that shows the next question on that thread routed afresh
- [ ] 4.3 Write a test that shows one unpinned thread answering a turn in each scope
- [ ] 4.4 Write a test that shows only the routed scope's tools offered to the model
- [ ] 4.5 Write a test that shows a deployment offering one scope routing nothing

## 5. Ambiguity, and a question that fits no scope

- [ ] 5.1 Write a test that shows an ambiguous question stopping the turn to ask which scope
- [ ] 5.2 Write a test that shows the turn answering under the scope the user chose
- [ ] 5.3 Write a test that shows a declined ambiguity answered in the default scope
- [ ] 5.4 Write a test that shows a question fitting no scope answered with only the
      system-wide instructions and tools
- [ ] 5.5 Write a test that shows the resumed ambiguous turn spending its whole round budget

## 6. The trace says what the turn was focused on

- [ ] 6.1 Write a test that shows the trace naming the scope and how it was settled
- [ ] 6.2 Write a test that shows that step surviving a checkpoint and the conversation store

## 7. The travel plugin

- [ ] 7.1 Write a test that shows the travel plugin registering instructions under its own
      scope, and nothing system-wide
- [ ] 7.2 Write a test that shows the travel plugin registering no tool
- [ ] 7.3 Write a test that shows a travel question answered from that plugin's own documents

## 8. What the deployment offers

- [ ] 8.1 Write a test that shows `CORA_SCOPES` read as the scopes a turn may run under
- [ ] 8.2 Write a test that shows a caller's own scopes winning over routing for one turn

## 9. The page

- [ ] 9.1 Write a test that shows the ask endpoint carrying a pin and fixing the thread's scope
- [ ] 9.2 Write a test that shows a session reporting the scope it is pinned to
- [ ] 9.3 Write a test that shows the endpoint refusing a second, different pin as a sentence
- [ ] 9.4 Write a test that shows the scope the turn ran under drawn on the page's trace
- [ ] 9.5 Bring the component-map guard green again over the walk this change lengthens
- [ ] 9.6 Bring the sequence-diagram guard green again over the two new steps

## 10. The router is measured

- [ ] 10.1 Write a test that shows the recorded set carrying a scope per question, asked alone
      and as a follow-up
- [ ] 10.2 Write a test that shows the report naming the share of scopes chosen rightly
- [ ] 10.3 Write a test that shows a share under the recorded threshold failing the `llm` tier

## 11. The marker comes off

- [ ] 11.1 Drop 1.1's `xfail` marker and watch the outer test pass
