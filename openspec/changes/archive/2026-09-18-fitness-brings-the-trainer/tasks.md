## 1. The outer test

- [x] 1.1 Write the functional test where the fitness plugin brings a page, a workout posted the way the trainer posts one lands in the fitness field, and a question about it is answered from that document, marked `@pytest.mark.xfail(strict=True)`.

## 2. The plugin brings it

- [x] 2.1 Write a test that the fitness plugin registers a page under its own field.
- [x] 2.2 Write a test that the directory it registers is the one shipped beside the module, holding an entry page.
- [x] 2.3 Write a test that the plugin still registers its instructions, its three tools and its medical screen.

## 3. Shipped with the plugin

- [x] 3.1 Write a guard that a plugin shipping files that are not Python has them in its wheel.

## 4. What the trainer writes

The page's own JavaScript, which only the browser tier runs: its functions are called in
the page rather than lifted out of the file.

- [x] 4.1 Write a test that a workout's text is a heading per exercise with its load, followed by its sets.
- [x] 4.2 Write a test that equal sets read as a count of them and unequal ones as each in turn.
- [x] 4.3 Write a test that an exercise carrying no weight reads as bodyweight.
- [x] 4.4 Write a test that two exercises are two headings, separated by a blank line.
- [x] 4.5 ~~An exercise nothing was logged for is not in the text, and nothing logged renders none.~~ Dropped as its own item: the filter is in the finishing rather than the rendering, and the browser test that finishes a one-exercise workout is what holds it.

## 5. Where it lands

- [x] 5.1 ~~The page reads its field out of the path it is served under.~~ Dropped as its own item: the page's `const` bindings are not reachable from a test, and 7.1 asserts the field it actually saved into.
- [x] 5.2 Write a test that finishing uploads the text under today's date into that field.
- [x] 5.3 Write a test that an upload cora refuses is reported, the workout left where it can be copied, and the page's own history holding it all the same.

## 6. Answering from it

- [x] 6.1 Write a test that a question in the fitness field is answered from an uploaded workout and cites it.

## 7. Through the browser

- [x] 7.1 Write a browser test that the fitness trainer is drawn when its field is fixed, a set is logged, and finishing puts a document in the field.

## 8. Found on review

- [x] 8.1 Write a test that only the exercises worked are in the text a workout hands over.
- [x] 8.2 Write a test that a workout with nothing logged uploads nothing and says so.
- [x] 8.3 Write a test that every host the page reaches is one the plugin's suite names.
- [x] 8.4 Write a test that the plan ships named in the language the coach answers in.

## 9. Close it

- [x] 9.1 Drop the outer test's `xfail` marker and watch it pass.
