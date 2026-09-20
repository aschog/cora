## 1. The outer test

Chromium is given a fake camera for this spec, the only one that needs it.

- [x] 1.1 Write a browser test that the opened camera fills the page, the header, the row, the sets and the weight drawn over it, marked `test.fail()` while in flight.

## 2. What stays in the frame

- [x] 2.1 ~~Write a browser test that the mirror control and the set count sit between the exercise row and the sets while the picture fills the page.~~ Folded into 1.1: the band is where the outer test looks for the mirror control and the rest, and a test green before the pin is not an increment.

## 3. Close it

- [x] 3.1 Drop the marker and watch the outer test pass.

## 4. The whole screen

- [x] 4.1 Write a browser test that the camera opened in the shell with both rails folded is the whole screen, and closing it gives the rails their place back, marked `test.fail()` while in flight.
- [x] 4.2 Write a test that the shell draws the frame over everything while a page asks for the screen and both rails are folded, and where it was with a rail open or once the page lets go.
- [ ] 4.3 Drop the marker and watch the browser test pass.
