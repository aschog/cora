Every item is one failing test. The README carries no item: a `.md` file is prose, held
by a person reading it. The page's items are `vitest`, the rest are `pytest`.

## 1. The outer test

- [x] 1.1 **Outer.** A field holding two documents, one deleted, gone from the listing,
      answering no search, its file off disk, and the other still answering —
      `tests/acceptance/test_documents.py`, marked `@pytest.mark.xfail(strict=True)`

## 2. One upload's passages leave the index

- [x] 2.1 A forgotten upload's passages coming back from no query of that field
- [x] 2.2 The field's listing dropping the name that upload was the last of
- [x] 2.3 The other uploads of that field untouched
- [x] 2.4 An upload nothing indexed forgotten without complaint
- [x] 2.5 Which uploads a name covers, answered for one name uploaded twice
- [x] 2.6 A name nothing was uploaded under covering none
- [x] 2.7 A store that cannot be reached raising the failure this adapter translates

## 3. One upload's file leaves the directory

- [x] 3.1 A forgotten upload's file gone, and its text read back as nothing
- [x] 3.2 The other uploads' files left where they are
- [x] 3.3 An upload no file was kept for forgotten without complaint
- [x] 3.4 A scope that could walk out of the root refused, as it is on the way in
- [x] 3.5 A store that cannot be written raising the failure this adapter translates

## 4. One call over both halves

- [ ] 4.1 Deleting a name dropping its passages and its file in one call
- [ ] 4.2 A name uploaded twice taking both uploads with it
- [ ] 4.3 The index dropped before the file, so a failure leaves nothing reachable
- [ ] 4.4 The same field's other documents, and another field's copy, both untouched
- [ ] 4.5 A deleted document indexed again when the same file is uploaded

## 5. The endpoint

- [ ] 5.1 `DELETE /api/documents/{scope}/{name}` answering `204`, with the name off the listing
- [ ] 5.2 A field this deployment never loaded refused, as every route taking a field does
- [ ] 5.3 A store that went away answering `503` and its own sentence
- [ ] 5.4 A citation into a deleted document answering the sentence that covers both cases

## 6. The rail

- [ ] 6.1 Each listed document drawing the control the other rails draw, named for it
- [ ] 6.2 The control asking rather than deleting, with nothing asked of cora
- [ ] 6.3 A confirmed question deleting that document and redrawing the list without it
- [ ] 6.4 Keeping the document deleting nothing, and asking again next time
- [ ] 6.5 The source panel cleared where what it was reading is what went
- [ ] 6.6 A delete that fails saying so, with the document still listed

## 7. Done

- [ ] 7.1 Drop 1.1's `xfail` marker and watch the outer test pass
