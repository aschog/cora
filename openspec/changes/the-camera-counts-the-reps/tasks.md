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

## 3. The readout

- [x] 3.1 Write a test that the count shows over the frame while the overlay is on.
- [x] 3.2 Write a test that it is hidden with the overlay off.
- [ ] 3.3 Write a test that it is hidden while a rest is running.
- [ ] 3.4 Write a test that logging a set puts the count back to nought.
- [ ] 3.5 Write a test that moving to another exercise puts the count back to nought.
- [ ] 3.6 Write a test that the sets keep the reps the plan and the taps gave them.

## 4. The finish

- [ ] 4.1 Drop the outer test's `test.fail()` and watch it pass.
