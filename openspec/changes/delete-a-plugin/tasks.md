## 1. The outer test

- [ ] 1.1 Write the outer functional test, `xfail(strict=True)`: deleting a dropped
      plugin from the page leaves no entry, no documents and no pinned conversation.

## 2. Removing the entry

- [ ] 2.1 Write a test that shows a dropped `.py` file's entry is deleted.
- [ ] 2.2 Write a test that shows a dropped package folder is deleted whole.
- [ ] 2.3 Write a test that shows a symlink is unlinked and what it points at is
      untouched.
- [ ] 2.4 Write a test that shows the entry goes last, so a failed document delete
      leaves the plugin loaded.

## 3. The cascade

- [ ] 3.1 Write a test that shows the documents of the plugin's field are gone from
      the listing.
- [ ] 3.2 Write a test that shows their passages are gone from the index.
- [ ] 3.3 Write a test that shows a plugin registering two fields empties both.
- [ ] 3.4 Write a test that shows a conversation pinned to the field is gone, turns
      and thread alike.
- [ ] 3.5 Write a test that shows an unpinned conversation is left where it is.
- [ ] 3.6 Write a test that shows another plugin's field, documents and conversations
      are untouched.
- [ ] 3.7 Write a test that shows what cora remembers and what an effect wrote are
      untouched.
- [ ] 3.8 Write a test that shows a field two loaded plugins bring keeps its documents.
- [ ] 3.9 Write a test that shows a plugin registering no field is deleted by its
      entry alone.

## 4. What a delete refuses

- [ ] 4.1 Write a test that shows a name nothing loaded is refused and deletes nothing.
- [ ] 4.2 Write a test that shows a plugin named in `CORA_PLUGINS` is refused as fixed
      at start.
- [ ] 4.3 Write a test that shows a name carrying a path or a traversal is refused.

## 5. The route

- [ ] 5.1 Write a test that shows `DELETE /api/plugins/{name}` removes the plugin and
      answers no content.
- [ ] 5.2 Write a test that shows a refused delete answers the sentence saying why.
- [ ] 5.3 Write a test that shows the plugin listing and the offered fields drop it on
      the next read.

## 6. The page

- [ ] 6.1 Write a test that shows a field brought by a deleteable plugin carries the
      control.
- [ ] 6.2 Write a test that shows a field with no plugin behind it carries none.
- [ ] 6.3 Write a test that shows the question names the plugin, its fields, and what
      stays.
- [ ] 6.4 Write a test that shows leaving the question deletes nothing.
- [ ] 6.5 Write a test that shows confirming reads the fields, the documents and the
      sessions again.

## 7. Done

- [ ] 7.1 Drop the outer test's `xfail` marker and watch it pass.
