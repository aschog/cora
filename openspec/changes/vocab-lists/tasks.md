## 1. The outer test

- [x] 1.1 Write the functional test where a photo's reading is kept as a named file of the vocab field, a second reading names the same file and adds to it, and the field drills the words of both without any of them being searchable, marked `@pytest.mark.xfail(strict=True)`.

## 2. The page reaches a field's files

- [x] 2.1 Write a test that the page reads the names a field holds.
- [x] 2.2 Write a test that the page reads one file by name.
- [x] 2.3 Write a test that the page writes a file, and reads back what it wrote.

## 3. The dialog

- [x] 3.1 Write a test that the dialog offers keeping the reading as a document or as a file.
- [x] 3.2 Write a test that keeping it as a document uploads it, as it does today.
- [x] 3.3 Write a test that keeping it as a file writes it under the name typed.
- [x] 3.4 Write a test that a file with no name cannot be kept.
- [x] 3.5 Write a test that the names the field holds are offered as the reader types.
- [x] 3.6 Write a test that naming a file that exists puts its text in the box above the reading.
- [x] 3.7 Write a test that what is kept is what the box holds after the reader has edited the merge.
- [x] 3.8 Write a test that a second photo read in one session does not carry the first one's name.

## 4. The composer

- [x] 4.1 Write a test that the ＋ opens a menu rather than the picker.
- [x] 4.2 Write a test that choosing from the menu opens the picker.
- [x] 4.3 Write a test that the menu closes on Escape and on a click outside it.

## 5. Vocab drills from files

- [x] 5.1 Write a test that the pairs a drill puts come from the field's files.
- [x] 5.2 Write a test that a list kept as a file is not among the field's documents.
- [x] 5.3 Write a test that a document uploaded to the vocab field is still searched and cited.
- [x] 5.4 Write a test that a field holding no files says so rather than failing.

## 6. A pair twice

- [x] 6.1 Write a test that a pair appearing twice on one list is drilled once.
- [x] 6.2 Write a test that a pair on two lists is drilled once per list.

## 7. Close it

- [x] 7.1 Drop the marker and watch the outer test pass.
