## 1. The outer test

- [x] 1.1 Write the browser test where a file added from the composer becomes a document of the conversation's field, marked as work in progress so the tier stays green.

## 2. The control

- [x] 2.1 Write a test that the composer draws a control for adding a file, labelled for what it does.
- [x] 2.2 Write a test that picking a file hands it to the upload the rail's control uses, with no second path.
- [x] 2.3 Write a test that the control says an upload is running while one is, and takes no second file until it is done.
- [x] 2.4 Write a test that a refused upload is reported where the rail reports one, and the control is usable again.

## 3. Both controls

- [x] 3.1 Write a test that the rail's control is still drawn and still uploads into the same field.

## 4. Close it

- [x] 4.1 Drop the marker and watch the browser test pass — it was held red by taking the wiring out rather than by a marker, since the tier has no xfail.
