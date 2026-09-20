## 1. The outer test

- [x] 1.1 Write the browser test where a photo added beside the question is read, corrected and saved as a document of that field, held red until the rest of the list is done.

## 2. The reading

- [x] 2.1 Write a test that an image is read into the text the reader recognised in it.
- [x] 2.2 Write a test that the reader is fetched once and reused by a second reading.
- [x] 2.3 Write a test that a reader that cannot be fetched fails saying that, and not that nothing was read.

## 3. What was read

- [x] 3.1 Write a test that the text read is drawn editable, with a way to save it and a way to discard it.
- [x] 3.2 Write a test that saving hands the upload a Markdown document named after the image.
- [x] 3.3 Write a test that what the reader edited is what is saved, not what was read.
- [x] 3.4 Write a test that discarding uploads nothing.
- [x] 3.5 Write a test that a photo holding no text says so rather than offering an empty document to save.

## 4. Which file goes where

- [x] 4.1 Write a test that a photo added is read, and a file that is not an image is uploaded as before.

## 5. Close it

- [x] 5.1 Let the outer browser test run and watch it pass.

## 6. Found on review

- [x] 6.1 Write a test that a second reading replaces the text the first one left in the box.
- [x] 6.2 Write a test that a click on the ground behind a corrected reading does not throw it away, and that an untouched one still closes.
- [x] 6.3 Write a test that a reader script which loaded and defined nothing is tried again for the next photo.
- [x] 6.4 Write a browser test that the control says a photo is being read and takes no second one until its reading is off the screen.
