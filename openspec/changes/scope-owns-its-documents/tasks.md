Every item is one failing test. Group 2 comes first because every other group needs the
file adapter to exist, and group 5 comes after the index so a scoped search has two
fields to tell apart.

`README.md`'s paragraph on the layout is not an item: prose is held by a person reading
it, not by a test. The component map is an item, because a guard is a test.

## 1. The outer test

- [ ] 1.1 **Outer.** Write a test that shows two fields each holding a document, a turn in
      one citing only its own field's passage, that field's listing naming only its own,
      and the citation opened from that field alone — `tests/acceptance/test_documents.py::`
      `test_a_field_answers_from_its_own_files`, marked `@pytest.mark.xfail(strict=True)`

## 2. A field is a directory of files

- [ ] 2.1 Write a test that shows keeping a document writing one Markdown file under the
      field's own directory
- [ ] 2.2 Write a test that shows an upload's text read back exactly as it was kept
- [ ] 2.3 Write a test that shows one filename uploaded twice becoming two files, each read
      back on its own
- [ ] 2.4 Write a test that shows one file kept in two fields as two files, neither reading
      the other's
- [ ] 2.5 Write a test that shows an upload never kept reading back as nothing
- [ ] 2.6 Write a test that shows a scope that is not a bare name refused rather than written
- [ ] 2.7 Write a test that shows a directory that cannot be written raising the port's own
      error

## 3. The index keeps a span, the file keeps the words

- [ ] 3.1 Write a test that shows an indexed passage carrying its span and no copy of its text
- [ ] 3.2 Write a test that shows a retrieved passage carrying the text at its span, as the
      file holds it
- [ ] 3.3 Write a test that shows a passage whose file is gone left out of what a search
      returns
- [ ] 3.4 Write a test that shows a passage carrying the field it was cut from, as it carries
      its upload
- [ ] 3.5 Write a test that shows a citation carrying that field through to the answer

## 4. A collection per field

- [ ] 4.1 Write a test that shows a document in one field never retrieved by a search of
      another
- [ ] 4.2 Write a test that shows a search of an empty field finding nothing and saying
      nothing was uploaded
- [ ] 4.3 Write a test that shows the sources listed for a field being that field's alone
- [ ] 4.4 Write a test that shows the same bytes ingested into two fields indexed in both

## 5. The turn's field reaches the search

- [ ] 5.1 Write a test that shows a tool call under a field searching that field's documents
- [ ] 5.2 Write a test that shows a search with no field bound reading the default field
- [ ] 5.3 Write a test that shows a plugin reading `Host.documents` inside a call searching
      the turn's field
- [ ] 5.4 Write a test that shows a delegated loop's own search reading the turn's field
- [ ] 5.5 Write a test that shows the binding gone once the call has returned

## 6. An upload names its field

- [ ] 6.1 Write a test that shows an upload naming a field landing in it and retrieved there
- [ ] 6.2 Write a test that shows an upload naming no field landing in the default field and
      retrieved there
- [ ] 6.3 Write a test that shows an upload naming an unloaded field refused, naming the
      fields there are
- [ ] 6.4 Write a test that shows a scope carrying a path separator refused at the door
- [ ] 6.5 Write a test that shows the listing route answering with one field's documents
- [ ] 6.6 Write a test that shows the upload route opening a citation from the field it was
      cut from

## 7. The page says which field a document goes into

- [ ] 7.1 Write a test that shows the rail offering the loaded fields and the default one
- [ ] 7.2 Write a test that shows a pinned thread uploading into its own field without asking
- [ ] 7.3 Write a test that shows a deployment with no fields asking nothing and using the
      default
- [ ] 7.4 Write a test that shows the rail listing the field it is showing
- [ ] 7.5 Write a test that shows a citation opened against the field it carries

## 8. The guards

- [ ] 8.1 Write a test that shows the component map matching the assembly the change leaves

## 9. Done

- [ ] 9.1 Drop the outer test's `xfail` marker and watch it pass
