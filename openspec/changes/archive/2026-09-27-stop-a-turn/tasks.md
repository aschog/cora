## 1. The outer test

- [x] 1.1 Write the outer test, marked `xfail(strict=True)`: a reader who stops reading a streamed turn mid-round leaves the model unasked for the round that would have followed.

## 2. The turn let go

- [x] 2.1 Write a test that a turn whose reader has gone takes no further step.
- [x] 2.2 Write a test that a turn stopped mid-prose ends at the next piece rather than the next step.
- [x] 2.3 Write a test that a stopped turn is recorded in no conversation.
- [x] 2.4 Write a test that a turn nobody stopped still streams its steps and its answer.

## 3. The page

- [x] 3.1 Write a test that an aborted `ask` rejects with the sentence saying the reader stopped it.
- [x] 3.2 Write a test that the composer's control stops the turn while one runs, and asks a question while none does.
- [x] 3.3 Write a test that stopping leaves the question under that sentence, with no answer beside it.
- [x] 3.4 Write a test that the composer takes the next question once a turn has been stopped.
- [x] 3.5 Write the browser test that a turn stopped mid-answer gives the conversation back.

## 4. The outer test again

Dropped after 2.1 rather than last, because the outer test reaches only the streamed
turn and that item finishes it.

- [x] 4.1 Drop the marker and watch the outer test pass.
