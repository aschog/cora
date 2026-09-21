## 1. The outer tests

Chromium is given a fake camera for the one spec that needs it.

- [x] 1.1 Write a browser test that the opened camera fills the page with the controls drawn over it, marked `test.fail()`.
- [x] 1.2 Write a browser test that the camera in the shell with both rails folded is the whole screen, marked `test.fail()`.

## 2. The shell's part

- [x] 2.1 Write a test that the shell hides the folded rails while a page asks, and draws them again once it lets go.

## 3. Found on review

- [x] 3.1 Write a test that a message from another origin does not take the screen.
- [x] 3.2 Write a test that a page changed for another takes its asking with it.
- [x] 3.3 Write a browser test that the shell moves only once the picture is there.
- [x] 3.4 Write a browser test that a camera closed, or closed and reopened, while the browser asks keeps one stream.
- [x] 3.5 Write a browser test that the frame keeps its ground while the browser asks.
- [x] 3.6 Write a browser test that a picture taken away closes the camera and lets the screen go.
- [x] 3.7 Hit-test each control group above the picture, and watch the test fail with the lifting rule gone.

- [x] 3.8 Write a test that Escape gives the shell its screen back whatever the page does.
- [x] 3.9 Write a browser test that a permission alone moves nothing, and the first frame is what takes the screen.

## 4. Close it

- [x] 4.1 Drop both markers and watch the outer tests pass.
