## 1. The outer test

- [x] 1.1 Write the functional test where a plugin's handler answers a question in its field and the reader reads it with the model never asked, a question it leaves alone is answered by the model, and the taken turn is in the transcript the model reads next, marked `@pytest.mark.xfail(strict=True)`.

## 2. The event

- [ ] 2.1 Write a test that the taking event is one a plugin may subscribe to, and the table of points has six.
- [ ] 2.2 Write a test that the first handler to answer with text ends the dispatch with that text, and the ones after it do not run.
- [ ] 2.3 Write a test that a dispatch nobody took answers with nothing.
- [ ] 2.4 Write a test that a handler answering with something that is not text is dropped, traced as broke, and the next one still runs.
- [ ] 2.5 Write a test that a handler that raises is dropped, the dispatch goes on, and the trace holds the kind of the exception and not its message.
- [ ] 2.6 Write a test that a handler answering with blank text has answered nothing.

## 3. The step

- [ ] 3.1 Write a test that the step contributes the handler's text as this turn's assistant message, and a trace naming the plugin.
- [ ] 3.2 Write a test that the step contributes no message where no handler took the question.
- [ ] 3.3 Write a test that a handler is handed the question and runs in the turn's field.
- [ ] 3.4 Write a test that what a handler kept while taking is in the state the step contributes, and what an earlier turn kept is readable there.
- [ ] 3.5 Write a test that a handler registered under another field is not offered the question.

## 4. The route out of the marker

- [ ] 4.1 Write a test that the opening route answers done once this turn holds an assistant message and rounds where it holds none.
- [ ] 4.2 Write a test that the runner walks a turn whose marker answered straight to the answer step, and the model never runs.
- [ ] 4.3 Write a test that a turn whose marker answered nothing walks the model and its rounds as before.
- [ ] 4.4 Write a test that the answer step settles what the marker wrote, offered to the answer handlers first.

## 5. The drawing

- [ ] 5.1 Write a guard that the round map calls the opening route after the work step and ahead of the model, as the runner declares it.

## 6. Close it

- [ ] 6.1 Drop the marker and watch the outer test pass.
