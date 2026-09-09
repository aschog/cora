# Tasks

The rule landed already, in `bb36f62` on `fix/upload-selection-and-one-value-asks`. This
list is what a review of that commit found, and what makes the code match the delta.

## 1. The story, end to end

- [x] 1.1 Write the outer test, `xfail(strict=True)`: a turn asking for one value answers
      in prose and stops on nothing, while a card of one read-only field still stops it.

## 2. The rule counts what the reader may write

- [x] 2.1 Write a test that a card of one read-only field is put to the reader, and the
      call runs on what they confirm.
- [x] 2.2 Write a test that a card of one writable field beside one read-only field is
      refused, so the count is of writable fields and not of the difference.

## 3. The model is bound where it reads

- [x] 3.1 Write a test that the form tool's offered schema refuses a single field.
- [x] 3.2 Write a test that a one-field form is refused in the words that say what to do
      instead, rather than in the schema's own "is too short".
- [x] 3.3 Write a test that a round repeating a one-field form still ends in an answer,
      each refusal a call that failed on the trace.

## 4. A refused card is on the trace

- [x] 4.1 Write a test that a plugin's card refused for asking one value leaves a failed
      step on the trace, naming the tool and the value.

## 5. The fixtures and the prose

- [x] 5.1 Write a test that the gate fixture's tool takes every argument its card asks
      for, so a card cannot ask for what its schema does not declare.
- [x] 5.2 Write a test that a schema asked over yields a field per property however many
      are known, which is what the how-to's `asks` example turns on.

## 7. What a card that asked for nothing settles

- [x] 7.1 Write a test that a card of read-only fields, confirmed, does not tell the
      model the reader filled the call in with nothing.
- [x] 7.2 Write a test that the same card, left, tells the model it was not confirmed
      rather than that a value was withheld.
- [x] 7.3 Write a test that a card of one writable field already holding a value is
      refused too, so the count is blind to what is in the box.

## 8. The page, as a second review found it

- [x] 8.1 Write a test that an upload whose request fails leaves nothing indexing, with
      the row seen arriving first — the one it had passed without ever drawing.
- [x] 8.2 Write a test that a row is drawn in the field it was uploaded into and in no
      other, which nothing held.
- [x] 8.3 Write a test that the upload control still says what it does while a file is
      indexing, rather than being renamed by the count.
- [x] 8.4 Write a test that a document just indexed is said in the live region, because
      a row leaving one is not announced.
- [x] 8.5 Make the browser tier assert the row appears under the control, rather than
      that an empty region is empty.

## 6. Done

- [x] 6.1 Drop 1.1's marker and watch the outer test pass — early, because item 2 is
      what the outer criterion turned on and items 3 to 5 are the rest of the findings.
