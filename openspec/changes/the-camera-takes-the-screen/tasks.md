## 1. The outer test

Chromium is given a fake camera for this spec, the only one that needs it.

- [x] 1.1 Write a browser test that the opened camera fills the page, the header, the row, the sets and the weight drawn over it, marked `test.fail()` while in flight.

## 2. What stays in the frame

- [x] 2.1 ~~Write a browser test that the mirror control and the set count sit between the exercise row and the sets while the picture fills the page.~~ Folded into 1.1: the band is where the outer test looks for the mirror control and the rest, and a test green before the pin is not an increment.

## 3. Close it

- [x] 3.1 Drop the marker and watch the outer test pass.

## 4. The whole screen

The shell's part is the frontend delta: a page asks, and the shell answers while both rails are folded.

- [x] 4.1 Write a browser test that the camera opened in the shell with both rails folded is the whole screen, and closing it gives the rails their place back, marked `test.fail()` while in flight.
- [x] 4.2 Write a test that the shell hides what is left of the folded rails while a page asks for the screen, and draws them again with a rail open or once the page lets go.
- [x] 4.3 Drop the marker and watch the browser test pass.

## 5. Found on review

- [x] 5.1 Write a test that a message from another origin does not take the screen, and that a page loaded again has let it go.
- [x] 5.2 Write a browser test that the shell moves only once the picture is there, and that a camera closed while the browser was asking stays closed.
- [x] 5.3 Strengthen the browser test so each control group is hit-tested above the picture, and watch it fail with the lifting rule gone.
