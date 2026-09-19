## 1. The outer test

- [x] 1.1 Write the functional test where three trainer-posted workouts, two on one day, list as two dated sessions with their numbers and not the plan, marked `@pytest.mark.xfail(strict=True)`.

## 2. The grammar, read back

- [x] 2.1 Write a test that a heading ending in kilograms reads as a movement with that name and load.
- [x] 2.2 Write a test that a heading ending in `bw` or `bw+n` reads as a bodyweight load.
- [x] 2.3 Write a test that repeated sets read as N sets of R reps, and listed sets as each in turn.
- [x] 2.4 Write a test that a timed line reads as one set of left plus right reps.
- [x] 2.5 Write a test that a line that is neither heading nor sets is a note on the movement above it.
- [x] 2.6 Write a test that a heading without a load, or text before the first heading, refuses the document by line.
- [x] 2.7 Write a test that reps sum the sets, volume is load times reps, and a bodyweight movement has none.
- [x] 2.8 Write a test that a heading in another script reads as any other.

## 3. What the tool lists

- [x] 3.1 Write a test that every document named for a day is a session dated from its name, oldest first.
- [x] 3.2 Write a test that two documents of one day are one session, movements in upload order.
- [x] 3.3 Write a test that a document not named for a day is not a session.
- [x] 3.4 Write a test that a dated document the grammar refuses is left out and said so on the trace.
- [ ] 3.5 Write a test that an exercise keeps only its movements, whatever the case, and drops a session left empty.
- [ ] 3.6 Write a test that a day drops the sessions before it.
- [ ] 3.7 Write a test that a movement says whether it rose on the previous session of that exercise.
- [ ] 3.8 Write a test that nothing logged answers in words rather than an empty list.

## 4. The field offers it

- [ ] 4.1 Write a test that the plugin registers a fourth tool under its field, `list_workouts`, with no effect.
- [ ] 4.2 Write a test that the brief tells the coach to list what was trained and to search the rest.

## 5. Close it

- [ ] 5.1 Drop the outer test's `xfail` marker and watch it pass.
