Every item is one failing test, and group 2 comes first because the rest are written
against it.

## 1. The outer test

- [x] 1.1 **Outer.** Write a test that shows a turn names *screen*, *work* and *answer*,
      in order, through `Agent.answer`. Mark it `@pytest.mark.xfail(strict=True)`

## 2. A step has a name

- [x] 2.1 Write a test that shows a named step contributes a trace step carrying its
      name first
- [x] 2.2 Write a test that shows a `CoreError` from a named step carries that step's
      name
- [x] 2.3 Write a test that shows the sentence a user reads is unchanged by that name
- [x] 2.4 Write a test that shows a foreign exception leaves a named step untagged and
      unswallowed

## 3. What each step is responsible for

- [x] 3.1 Write a test that shows the screening step refuses before the thread is
      written or the model called
- [x] 3.2 Write a test that shows the screening step opens the turn: transcript, marks
      and brief
- [x] 3.3 Write a test that shows the answering step settles the answer from the round
      that ended
- [x] 3.4 Write a test that shows a state short of the answering step carries no answer

## 4. The turn as one walk

- [x] 4.1 Write a test that shows the runner walks screen → work → answer, yielding a
      state per step
- [x] 4.2 Write a test that shows every round falls inside the working step's marker
- [x] 4.3 Write a test that shows neither the screening nor the answering step takes a
      round
- [x] 4.4 Write a test that shows the transcript holds one copy of the question and each
      message
- [x] 4.5 Write a test that shows a turn parks from inside the working step, visible on
      the thread
- [x] 4.6 Write a test that shows a resumed turn does not re-run the tool that ran before
      it stopped
- [x] 4.7 Write a test that shows a caller sees a round's decision before the turn has
      finished
- [x] 4.8 Write a test that shows a spent budget trips the core's limit, not the
      recursion guard
- [x] 4.9 Write a test that shows a thread whose turn failed part-way answers the next
      question
- [x] 4.10 Write a test that shows what was said before the failure is still on the
      thread

## 5. The sequence is the extension point

- [x] 5.1 Write a test that shows story 6's added step is walked in its place, with the
      runner unchanged
- [x] 5.2 Write a test that shows the graph reader behind the session maps finds the
      walk and the loop inside it

## 6. The marker comes off

- [x] 6.1 Drop 1.1's `xfail` marker and watch the outer test pass
