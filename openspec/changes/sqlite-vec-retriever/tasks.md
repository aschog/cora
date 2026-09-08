## 1. The outer test

- [x] 1.1 Write the acceptance test — a document ingested and searched in each of two
  fields, with the index one SQLite file at the configured path — marked
  `@pytest.mark.xfail(strict=True)`.

## 2. The store round-trips

- [x] 2.1 Write a test that passages added with our own embeddings come back from a
  query of them.
- [x] 2.2 Write a test that a store nothing was added to returns nothing at all.
- [x] 2.3 Write a test that the vector table takes its width from the first vector
  written, not a constant.
- [x] 2.4 Write a test that asking for more neighbours than exist returns the ones
  that do.
- [x] 2.5 Write a test that a score comes back between nought and one, nearest first.
- [x] 2.6 Write a test that a retrieved passage carries its span and no text.

## 3. A field is its own

- [x] 3.1 Write a test that a passage of one field is unreachable from a query in
  another.
- [x] 3.2 Write a test that an empty field answers empty while another field holds
  passages.
- [x] 3.3 Write a test that sources and contains read only the field they were asked
  for.

## 4. Forgetting an upload

- [x] 4.1 Write a test that a forgotten upload comes back from no query.
- [x] 4.2 Write a test that forgetting one upload leaves the other uploads of its name.
- [x] 4.3 Write a test that forgetting an upload nothing indexed is not an error.
- [x] 4.4 Write a test that the uploads of one name are read back by that name.
- [x] 4.5 Write a test that a name nothing was uploaded under covers no uploads.

## 5. Durability and failure

- [x] 5.1 Write a test that what was added is read back by a fresh adapter on the same
  file.
- [x] 5.2 Write a test that re-adding the same upload leaves one copy of each passage.
- [x] 5.3 Write a test that a store error surfaces as `RetrievalError`.
- [x] 5.4 Write a test that a path that cannot be opened surfaces as `RetrievalError`.
- [x] 5.5 Write a test that a connection refusing extensions surfaces as
  `RetrievalError` at construction.

## 6. Room for a second user

- [x] 6.1 Write a test that a written passage carries the user `local`.

## 7. Chroma leaves

- [x] 7.1 Write a config test that the index path defaults to a file under `.cora`.
- [x] 7.2 Write a guard that nothing in the workspace resolves `chromadb`.
- [x] 7.3 Update the reference-page guard to name the new adapter module and watch it
  pass.
- [x] 7.4 Redraw the component, upload and search maps until their guards pass.
- [x] 7.5 Discovered: the privacy page's store guard is red until the page names the
  index's new location.

## 8. Done

- [x] 8.1 Drop the `xfail` marker from 1.1 and watch the outer test pass.
