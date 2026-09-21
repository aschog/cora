## 1. The outer test

- [ ] 1.1 Write the functional test where a photo's reading is kept as a named file of the vocab field, a second reading names the same file and adds to it, and the field drills the words of both without any of them being searchable, marked `@pytest.mark.xfail(strict=True)`.

## 2. The page reaches a field's files

- [ ] 2.1 Write a test that the page reads the names a field holds.
- [ ] 2.2 Write a test that the page reads one file by name.
- [ ] 2.3 Write a test that the page writes a file, and reads back what it wrote.

## 3. The dialog

- [ ] 3.1 Write a test that the dialog offers keeping the reading as a document or as a file.
- [ ] 3.2 Write a test that keeping it as a document uploads it, as it does today.
- [ ] 3.3 Write a test that keeping it as a file writes it under the name typed.
- [ ] 3.4 Write a test that a file with no name cannot be kept.
- [ ] 3.5 Write a test that the names the field holds are offered as the reader types.
- [ ] 3.6 Write a test that naming a file that exists puts its text in the box above the reading.
- [ ] 3.7 Write a test that what is kept is what the box holds after the reader has edited the merge.
- [ ] 3.8 Write a test that a second photo read in one session does not carry the first one's name.

## 4. The composer

- [ ] 4.1 Write a test that the ＋ opens a menu rather than the picker.
- [ ] 4.2 Write a test that choosing from the menu opens the picker.
- [ ] 4.3 Write a test that the menu closes on Escape and on a click outside it.

## 5. Vocab drills from files

- [ ] 5.1 Write a test that the pairs a drill puts come from the field's files.
- [ ] 5.2 Write a test that a list kept as a file is not among the field's documents.
- [ ] 5.3 Write a test that a document uploaded to the vocab field is still searched and cited.
- [ ] 5.4 Write a test that a field holding no files says so rather than failing.

## 6. A pair twice

- [ ] 6.1 Write a test that a pair appearing twice on one list is drilled once.
- [ ] 6.2 Write a test that a pair on two lists is drilled once per list.

## 7. Close it

- [ ] 7.1 Drop the marker and watch the outer test pass.
