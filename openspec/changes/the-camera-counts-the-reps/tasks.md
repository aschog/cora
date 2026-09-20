The page's JavaScript runs in the browser tier only, so every item here is a Playwright
test in `frontends/react/ui/e2e/trainer.spec.ts`. That tier has no `xfail`, so the outer
test is held with `test.fail()` until the list is done.

## 1. The outer test

- [x] 1.1 Write the outer test — the overlay on, a written sequence of landmark frames
      fed to the page, and the count over the frame rising one a cycle — under `test.fail()`.

## 2. The counter

- [x] 2.1 Write a test that the counter reads nought before it is given a frame.
- [x] 2.2 Write a test that a sequence swinging one wrist up and down counts one a cycle.
- [x] 2.3 Write a test that the same sequence at half the size counts the same.
- [x] 2.4 Write a test that a sequence sliding bodily across the frame counts nothing.
- [x] 2.5 Write a test that a sequence moving the shoulders over planted wrists counts one a cycle.
- [x] 2.6 Write a test that a swing under the amplitude gate counts nothing.
- [x] 2.7 Write a test that two turning points inside the minimum period count one.
- [x] 2.8 Write a test that a frame the model found nobody in is skipped, not counted.
- [x] 2.9 Write a test that a wrist travelling a circle counts one a circle.
- [x] 2.10 Write a test that the frame the overlay draws is the frame the counter is
      given — found in flight, because nothing fed the counter at all. It pins the door,
      not the pose loop's call to it, which no test reaches.

## 3. The readout

- [x] 3.1 Write a test that the count shows over the frame while the overlay is on.
- [x] 3.2 Write a test that it is hidden with the overlay off.
- [x] 3.3 Write a test that it is hidden while a rest is running.
- [x] 3.4 Write a test that logging a set puts the count back to nought.
- [x] 3.5 Write a test that moving to another exercise puts the count back to nought.
- [x] 3.6 Write a test that the sets keep the reps the plan and the taps gave them.

## 4. The finish

- [x] 4.1 Drop the outer test's `test.fail()` and watch it pass.

## 5. The review's findings

- [x] 5.1 Write a test that a rest standing over the frame is not counted through.
- [x] 5.2 Write a test that a workout cora took leaves no count behind.
- [x] 5.3 Write a test that un-logging a set leaves the count where it was.
- [x] 5.4 Write a test that the row already in the frame does not start the count over.
- [x] 5.5 Write a test that tapping another row does.
- [x] 5.6 Make 2.1's test read the count before a frame is given, not after a reset.
- [x] 5.7 Write a test that a movement the arms do not make against the torso counts
      nothing, so the counter's ceiling is a specified limit and not a silence.
- [x] 5.8 Write a test that the same travel counts the same across the frame as down it.
- [x] 5.9 Write a test, on landmarks recorded off the camera, that a set of one-arm
      swings counts at the pace it was lifted — found by running it, not by the suite.
- [x] 5.10 Write a test that the arm which is not working adds no reps of its own.

## 6. Still open

Run on a real camera after the handover fix, the count is still wrong. The suite is
green on recorded landmarks, so whatever is left is something the tape did not catch.
This change does not archive until it is closed.

- [ ] 6.1 Characterise what the count does against what was lifted — a fresh tape with a
      known number of reps, and the symptom named before anything is changed.
- [ ] 6.2 Write the failing test that reproduces it off recorded landmarks.
- [ ] 6.3 Decide whether a single raise-and-lower should count at all: reaching for the
      screen scores a rep today, which is the requirement never being written rather than
      the code disagreeing with it.
