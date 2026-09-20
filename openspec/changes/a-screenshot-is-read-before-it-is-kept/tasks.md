## 1. The outer test

- [ ] 1.1 Write the browser test where a photo added beside the question is read, corrected and saved as a document of that field, held red until the rest of the list is done.

## 2. The reading

- [ ] 2.1 Write a test that an image is read into the text the reader recognised in it.
- [ ] 2.2 Write a test that the reader is fetched once and reused by a second reading.
- [ ] 2.3 Write a test that a reader that cannot be fetched fails saying that, and not that nothing was read.

## 3. What was read

- [ ] 3.1 Write a test that the text read is drawn editable, with a way to save it and a way to discard it.
- [ ] 3.2 Write a test that saving hands the upload a Markdown document named after the image.
- [ ] 3.3 Write a test that what the reader edited is what is saved, not what was read.
- [ ] 3.4 Write a test that discarding uploads nothing.
- [ ] 3.5 Write a test that a photo holding no text says so rather than offering an empty document to save.

## 4. Which file goes where

- [ ] 4.1 Write a test that a photo added is read, and a file that is not an image is uploaded as before.

## 5. Close it

- [ ] 5.1 Let the outer browser test run and watch it pass.
