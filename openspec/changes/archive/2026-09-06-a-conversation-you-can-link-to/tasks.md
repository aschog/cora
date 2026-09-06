Written alongside the code rather than ahead of it: the change was retrofitted onto
reviewed work. The list is a record of the tests that hold it. Every item names a test
that exists and fails if its behaviour is removed.

## 1. The outer test

- [x] 1.1 Write the outer test: opening a conversation names it, and a page at that address opens in it.

## 2. Reading an address

- [x] 2.1 Write a test that a conversation is read back out of an address that names one.
- [x] 2.2 Write a test that an address naming none — empty, a fragment, the route with nothing after it — names none.
- [x] 2.3 Write a test that a thread decoding to `../memory` names no conversation.
- [x] 2.4 Write a test that a thread of letters, digits and dashes is read back whichever way it was minted.
- [x] 2.5 Write a test that an address that decodes to nothing names no conversation.
- [x] 2.6 Write a test that a refused address asks the store for nothing.

## 3. Writing an address

- [x] 3.1 Write a test that the conversation on the page is written into the address.
- [x] 3.2 Write a test that opening a different conversation adds an entry, so back leaves it.
- [x] 3.3 Write a test that opening the same one twice adds none.
- [x] 3.4 Write a test that a conversation acquiring a name replaces the entry it stands on.
- [x] 3.5 Write a test that starting over takes the conversation out of the address.

## 4. The page following it

- [x] 4.1 Write a test that the address changing under the page opens the conversation it names.
- [x] 4.2 Write a test that the address the page wrote itself does not open that conversation a second time.
- [x] 4.3 Write a test that a conversation the reader started is named once it has answered.
- [x] 4.4 Write a test that an answer landing in a conversation the reader left does not name it.
- [x] 4.5 Write a test that a card left open outranks the address.
- [x] 4.6 Write a test that a conversation paused on its first question is named once the card settles.

## 5. The outer test again

- [x] 5.1 Drop the marker and watch the outer test pass.
