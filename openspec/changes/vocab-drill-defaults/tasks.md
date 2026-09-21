## 1. The outer test

- [ ] 1.1 Write the functional test where a fresh conversation puts the German side with no question asked, runs one shuffled pass to its end without writing the schedule, and starts over when asked to go again, marked `@pytest.mark.xfail(strict=True)`.

## 2. German first

- [ ] 2.1 Write a test that the first word put is the left side, with nothing asked first.
- [ ] 2.2 Write a test that asking for the other side puts the right one from then on.
- [ ] 2.3 Write a test that the side asked for lasts the conversation and not beyond it.

## 3. The pass

- [ ] 3.1 Write a test that every word of the list is put once when each is answered right.
- [ ] 3.2 Write a test that a word missed is put again before the pass ends.
- [ ] 3.3 Write a test that two passes over one list differ in order.
- [ ] 3.4 Write a test that a pass covers the chosen list and no other.
- [ ] 3.5 Write a test that a finished pass says so rather than putting a word.
- [ ] 3.6 Write a test that going again puts words over the same list.

## 4. Spacing off

- [ ] 4.1 Write a test that answering a word with spacing off leaves the schedule untouched.
- [ ] 4.2 Write a test that turning spacing on moves the schedule as it does today.
- [ ] 4.3 Write a test that spacing turned on in one conversation is off again in the next.
- [ ] 4.4 Write a test that a drill with spacing off runs where the deployment keeps no store.

## 5. Close it

- [ ] 5.1 Drop the marker and watch the outer test pass.
