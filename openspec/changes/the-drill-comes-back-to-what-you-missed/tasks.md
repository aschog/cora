## 1. The outer test

- [x] 1.1 Write the functional test where a word missed in one conversation is the word put to the reader in another. Written red against the plugin as it stood rather than under a marker: the tools it calls did not exist, so a strict xfail would have passed on an import error.

## 2. The spacing

- [x] 2.1 Write a test that a word answered right the first time is due a day later.
- [x] 2.2 Write a test that a word answered right a second time is due six days later, and a third time by its ease.
- [x] 2.3 Write a test that a word missed is due again in the same session, whatever it had earned.
- [x] 2.4 Write a test that a miss lowers the ease, and that it never falls below the floor.
- [x] 2.5 Write a test that a word never drilled reads as due.

## 3. The schedule

- [x] 3.1 Write a test that a schedule written to the store reads back as the same words, intervals and dates.
- [x] 3.2 Write a test that a schedule the store never held reads as an empty one rather than failing.
- [x] 3.3 Write a test that answering one word leaves every other word's entry as it was.
- [x] 3.4 Write a test that text the store holds which is not a schedule reads as an empty one.

## 4. The words

- [x] 4.1 Write a test that the pairs are read out of a Markdown table, with what its header calls the two columns.
- [x] 4.2 Write a test that a document that is not a list contributes no pairs.
- [x] 4.3 Write a test that a list of lines — numbered, em-dashed, as the reading of a screenshot saves one — gives its pairs too. Found by drilling a real saved list: the drill said the field held nothing.
- [x] 4.4 Write a test that a word holding a hyphen is not split at it, and that two spaces or a tab are a gap.

## 5. The tools

- [x] 5.1 Write a test that asking for a word hands back the side being asked and not the side to produce.
- [x] 5.2 Write a test that a word due is preferred to a word not due, and a new word is due.
- [x] 5.3 Write a test that nothing due and nothing new says the session is done.
- [x] 5.4 Write a test that saying how it went moves that word's schedule in the store.
- [x] 5.5 Write a test that saying how a word nobody asked about went is refused rather than written.
- [x] 5.6 Write a test that a word already missed is put before a word never drilled — found by mutating the write away and watching the outer test stay green.

## 6. The field

- [x] 6.1 Write a test that the plugin registers the two tools under its own field, beside its instructions.
- [x] 6.2 Write a test that the instructions tell the model to drill through the tools and never to do the arithmetic.

## 7. Close it

- [x] 7.1 Drop the marker and watch the outer test pass.
