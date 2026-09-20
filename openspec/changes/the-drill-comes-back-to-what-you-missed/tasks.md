## 1. The outer test

- [ ] 1.1 Write the functional test where a word missed in one conversation is the word put to the reader in another, marked `@pytest.mark.xfail(strict=True)`.

## 2. The spacing

- [ ] 2.1 Write a test that a word answered right the first time is due a day later.
- [ ] 2.2 Write a test that a word answered right a second time is due six days later, and a third time by its ease.
- [ ] 2.3 Write a test that a word missed is due again in the same session, whatever it had earned.
- [ ] 2.4 Write a test that a miss lowers the ease, and that it never falls below the floor.
- [ ] 2.5 Write a test that a word never drilled reads as due.

## 3. The schedule

- [ ] 3.1 Write a test that a schedule written to the store reads back as the same words, intervals and dates.
- [ ] 3.2 Write a test that a schedule the store never held reads as an empty one rather than failing.
- [ ] 3.3 Write a test that answering one word leaves every other word's entry as it was.
- [ ] 3.4 Write a test that text the store holds which is not a schedule reads as an empty one.

## 4. The words

- [ ] 4.1 Write a test that the pairs are read out of the field's Markdown lists, with the heading's language.
- [ ] 4.2 Write a test that a document that is not a list contributes no pairs.

## 5. The tools

- [ ] 5.1 Write a test that asking for a word hands back the side being asked and not the side to produce.
- [ ] 5.2 Write a test that a word due is preferred to a word not due, and a new word is due.
- [ ] 5.3 Write a test that nothing due and nothing new says the session is done.
- [ ] 5.4 Write a test that saying how it went moves that word's schedule in the store.
- [ ] 5.5 Write a test that saying how a word nobody asked about went is refused rather than written.

## 6. The field

- [ ] 6.1 Write a test that the plugin registers the two tools under its own field, beside its instructions.
- [ ] 6.2 Write a test that the instructions tell the model to drill through the tools and never to do the arithmetic.

## 7. Close it

- [ ] 7.1 Drop the marker and watch the outer test pass.
