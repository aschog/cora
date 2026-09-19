## 1. The outer test

- [x] 1.1 Write the functional test where a plugin's tool is handed both documents of one name in its field and not another field's, marked `@pytest.mark.xfail(strict=True)`.

## 2. The knowledge base reads a field

- [ ] 2.1 Write a test that the knowledge base lists the running field's documents by name and text, in upload order.
- [ ] 2.2 Write a test that two uploads of one name are two documents.
- [ ] 2.3 Write a test that a document whose file is gone is left out and the rest come back.
- [ ] 2.4 Write a test that another field's document is not listed.
- [ ] 2.5 Write a test that a turn running in two fields is handed both fields' documents, each saying which.

## 3. Handed to the plugin

- [ ] 3.1 Write a test that the host's documents offer the listing, and a call that used it is labelled untrusted.

## 4. Close it

- [ ] 4.1 Drop the outer test's `xfail` marker and watch it pass.
