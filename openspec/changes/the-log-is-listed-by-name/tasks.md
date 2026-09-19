## 1. The outer test

- [x] 1.1 Write the functional test where three trainer-posted workouts list as two lines naming days and exercises, and in detail as movements with numbers, marked `@pytest.mark.xfail(strict=True)`.

## 2. Two views

- [ ] 2.1 Write a test that unasked for detail a session is its day and the exercises worked, each named once, in order, as text.
- [ ] 2.2 Write a test that asked for detail each movement is a line with load, sets, reps, volume and a mark where it rose.
- [ ] 2.3 Write a test that a bodyweight movement's line carries its reps and no volume.
- [ ] 2.4 Write a test that an exercise and a day narrow both views.

## 3. The field offers it

- [ ] 3.1 Write a test that the tool takes `detail` beside the two filters.
- [ ] 3.2 Write a test that the brief says to relay the listing as it is, untranslated, and detail only on request.

## 4. Close it

- [ ] 4.1 Drop the outer test's `xfail` marker and watch it pass.
