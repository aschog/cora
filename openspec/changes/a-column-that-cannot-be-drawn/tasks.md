Written alongside the code rather than ahead of it: this change was retrofitted onto work
already done and reviewed, so the list is a record of the tests that hold it. Every item
names a test that exists and fails if its behaviour is removed.

## 1. The outer test

- [x] 1.1 Write the functional test where a store answers with a shape a panel cannot read, and the reader is told that panel could not be drawn while the conversation stays on screen.

## 2. The boundary itself

- [x] 2.1 Write a test that what threw is replaced by the sentence it was given.
- [x] 2.2 Write a test that what did not throw is drawn as it was.
- [x] 2.3 Write a test that trying again draws children that no longer throw.
- [x] 2.4 Write a test that trying again over children that still throw says so again.

## 3. Where they go

- [x] 3.1 Write a test that a panel that threw leaves the conversation and the documents rail drawn.
- [x] 3.2 Write a test that the strip above a broken panel still chooses another one.
- [x] 3.3 Write a test that moving to another panel draws it rather than the sentence.

## 4. The outer test again

- [x] 4.1 Drop the marker and watch the outer test pass.
