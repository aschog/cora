## 1. The outer test

- [x] 1.1 Write the outer functional test, `xfail(strict=True)`: deleting a dropped
      plugin from the page leaves no entry, no documents and no pinned conversation.

## 2. Removing the entry

- [x] 2.1 Write a test that shows a dropped `.py` file's entry is deleted.
- [x] 2.2 Write a test that shows a dropped package folder is deleted whole.
- [x] 2.3 Write a test that shows a symlink is unlinked and what it points at is
      untouched.
- [x] 2.4 Write a test that shows the entry goes last, so a failed document delete
      leaves the plugin loaded.

## 3. The cascade

- [x] 3.1 Write a test that shows the documents of the plugin's field are gone from
      the listing.
- [x] 3.2 Write a test that shows their passages are gone from the index.
- [x] 3.3 Write a test that shows a plugin registering two fields empties both.
- [x] 3.4 Write a test that shows a conversation pinned to the field is gone, turns
      and thread alike.
- [x] 3.5 Write a test that shows an unpinned conversation is left where it is.
- [x] 3.6 Write a test that shows another plugin's field, documents and conversations
      are untouched.
- [x] 3.7 Write a test that shows what cora remembers and what an effect wrote are
      untouched.
- [x] 3.8 Write a test that shows a field two loaded plugins bring keeps its documents.
- [x] 3.9 Write a test that shows a plugin registering no field is deleted by its
      entry alone.
- [x] 3.10 Write a test that shows the field a bare cora answers in keeps its documents
      and its conversations.
- [x] 3.11 Write a test that shows a field the deployment configured keeps its
      documents.

## 4. What a delete refuses

- [x] 4.1 Write a test that shows a name nothing loaded is refused and deletes nothing.
- [x] 4.2 Write a test that shows a plugin named in `CORA_PLUGINS` is refused as fixed
      at start.
- [x] 4.3 Write a test that shows a name carrying a path or a traversal is refused.
- [x] 4.4 Write a test that shows an entry that could not be removed is refused in
      cora's own words rather than the filesystem's.

## 5. The route

- [x] 5.1 Write a test that shows `DELETE /api/plugins/{name}` removes the plugin and
      answers no content.
- [x] 5.2 Write a test that shows a refused delete answers the sentence saying why.
- [x] 5.3 Write a test that shows the plugin listing and the offered fields drop it on
      the next read.
- [x] 5.4 Write a test that shows the listing says which fields would go with each
      plugin.

## 6. The page

- [x] 6.1 Write a test that shows a field brought by a deleteable plugin carries the
      control.
- [x] 6.2 Write a test that shows a field with no plugin behind it carries none.
- [x] 6.3 Write a test that shows the question names the plugin, its fields, and what
      stays.
- [x] 6.4 Write a test that shows leaving the question deletes nothing.
- [x] 6.5 Write a test that shows confirming reads the fields, the documents and the
      sessions again.
- [x] 6.6 Write a test that shows the question names the field that goes and not the
      field another plugin also brings.
- [x] 6.7 Write a test that shows a deployment offering one field can still delete its
      plugin.

## 7. Done

- [x] 7.1 Drop the outer test's `xfail` marker and watch it pass.
