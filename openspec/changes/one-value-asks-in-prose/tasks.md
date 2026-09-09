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

- [ ] 3.1 Write a test that the form tool's offered schema refuses a single field.
- [ ] 3.2 Write a test that the form tool's description tells the model to ask for one
      value in its answer.
- [ ] 3.3 Write a test that a round repeating a one-field form still ends in an answer
      rather than spending the turn's rounds.

## 4. A refused card is on the trace

- [ ] 4.1 Write a test that a plugin's card refused for asking one value leaves a failed
      step on the trace, naming the tool and the value.

## 5. The fixtures and the prose

- [ ] 5.1 Write a test that the gate fixture's tool takes every argument its card asks
      for, so a card cannot ask for what its schema does not declare.
- [ ] 5.2 Write a guard test that the how-to's `asks` example still yields a card of two
      fields when called with one of its two arguments.

## 6. Done

- [x] 6.1 Drop 1.1's marker and watch the outer test pass — early, because item 2 is
      what the outer criterion turned on and items 3 to 5 are the rest of the findings.
