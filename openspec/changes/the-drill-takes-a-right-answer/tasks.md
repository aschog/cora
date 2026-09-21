## 1. The outer test

- [x] 1.1 Write the functional test where the model puts the first word, three right answers in a row each read the next word with the model never asked, and a hint asked for then reaches a model that reads the taken words, marked `@pytest.mark.xfail(strict=True)`.

## 2. Taking a right answer

- [x] 2.1 Write a test that the other side of the word on the table, answered, is taken: the next word comes back, the pass is a word shorter, and the word was recorded as produced.
- [x] 2.2 Write a test that case and a closing full stop do not stop an answer being right.
- [x] 2.3 Write a test that an answer that is not the word is left to the model and moves nothing.
- [x] 2.4 Write a test that `h` is left to the model.
- [x] 2.5 Write a test that the last word of a pass is left to the model even when answered right.
- [x] 2.6 Write a test that a spaced session is left to the model.
- [x] 2.7 Write a test that a right answer with the drill running the other way round is judged against the German side.
- [x] 2.8 Write a test that nothing on the table leaves every answer to the model.

## 3. A hint

- [x] 3.1 Write a test that a right answer given after the model was asked while the word stayed on the table is recorded as missed, and the word comes round again.
- [x] 3.2 Write a test that a right answer after the word moved through the model is recorded as right.

## 4. The field

- [x] 4.1 Write a test that the plugin registers the handler at the taking point, under its field.
- [x] 4.2 Write a test that the instructions say a right answer never reaches the model, and that the word on the table is the last one put.

## 5. Close it

- [x] 5.1 Drop the marker and watch the outer test pass.
