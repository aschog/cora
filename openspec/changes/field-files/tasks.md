## 1. The outer test

- [ ] 1.1 Write the functional test where the screen writes a file into a field, the field's plugin reads it back in a turn, and a search of that field returns no passage of it, marked `@pytest.mark.xfail(strict=True)`.

## 2. The directory

- [ ] 2.1 Write a test that text written under a name is read back from a fresh adapter over the same directory.
- [ ] 2.2 Write a test that one plugin under two fields keeps two files under one name, and reads each field's own.
- [ ] 2.3 Write a test that a name nothing was written under reads as nothing.
- [ ] 2.4 Write a test that writing nothing under a name drops it, and the name stops being listed.
- [ ] 2.5 Write a test that listing a field's names returns them and no other field's.
- [ ] 2.6 Write a test that listing a field nothing was written into comes back empty rather than failing.
- [ ] 2.7 Write a test that a directory that cannot be written raises the failure cora reports rather than losing the write.

## 3. The name is one plain name

- [ ] 3.1 Write a test that a name containing a path separator is refused and writes nothing.
- [ ] 3.2 Write a test that a name containing `..` is refused and nothing outside the directory changes.
- [ ] 3.3 Write a test that an absolute name is refused.
- [ ] 3.4 Write a test that a refused name is refused on read and on drop as well as on write.

## 4. The cap

- [ ] 4.1 Write a test that a write over the cap is refused and keeps nothing.
- [ ] 4.2 Write a test that the refusal names the cap.

## 5. What the plugin is handed

- [ ] 5.1 Write a test that the host hands a plugin the files of the field the turn runs in.
- [ ] 5.2 Write a test that a plugin cannot reach a field the turn is not running in.

## 6. The routes

- [ ] 6.1 Write a test that a write to a field's files is read back by that field's plugin.
- [ ] 6.2 Write a test that listing a field's files returns the names it holds.
- [ ] 6.3 Write a test that reading a file by name returns what was written.
- [ ] 6.4 Write a test that a second write under one name replaces the first.
- [ ] 6.5 Write a test that a route refuses a name that is not one plain segment.
- [ ] 6.6 Write a test that reading a name nothing was written under answers as missing rather than failing.
- [ ] 6.7 Write a test that deleting a name leaves it unlisted and unreadable.
- [ ] 6.8 Write a test that deleting a name nothing was written under does not fail.
- [ ] 6.9 Write a test that deleting a name in one field leaves another field's file of that name standing.

## 7. Not a document

- [ ] 7.1 Write a test that a file written into a field is not returned by a search of that field.
- [ ] 7.2 Write a test that a file written into a field is not listed among that field's documents.
- [ ] 7.3 Write a test that deleting a field's documents leaves its files standing.

## 8. Assembled

- [ ] 8.1 Write a test that an app assembled with a files root hands every plugin the files of its field.
- [ ] 8.2 Write a test that the guard still holds with the new port under `cora.ports`.

## 9. Close it

- [ ] 9.1 Drop the marker and watch the outer test pass.
