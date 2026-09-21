## 1. The outer test

- [x] 1.1 Write the functional test where a fresh conversation puts the German side with no question asked, runs one shuffled pass to its end without writing the schedule, and starts over when asked to go again, marked `@pytest.mark.xfail(strict=True)`.

## 2. German first

- [x] 2.1 Write a test that the first word put is the left side, with nothing asked first.
- [x] 2.2 Write a test that asking for the other side puts the right one from then on.
- [x] 2.3 Write a test that the side asked for lasts the conversation and not beyond it.

## 3. The pass

- [x] 3.1 Write a test that every word of the list is put once when each is answered right.
- [x] 3.2 Write a test that a word missed is put again before the pass ends.
- [x] 3.3 Write a test that two passes over one list differ in order.
- [x] 3.4 Write a test that a pass covers the chosen list and no other.
- [x] 3.5 Write a test that a finished pass says so rather than putting a word.
- [x] 3.6 Write a test that going again puts words over the same list.

## 4. Spacing off

- [x] 4.1 Write a test that answering a word with spacing off leaves the schedule untouched.
- [x] 4.2 Write a test that turning spacing on moves the schedule as it does today.
- [x] 4.3 Write a test that spacing turned on in one conversation is off again in the next.
- [x] 4.4 Write a test that a drill with spacing off runs where the deployment keeps no store.

## 5. Close it

- [x] 5.1 Drop the marker and watch the outer test pass.
