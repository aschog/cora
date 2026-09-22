## 1. The outer test

- [x] 1.1 Write the outer test: a conversation answered once is listed at `/api/conversations` and read back from there, and `/api/sessions` answers nothing, marked `xfail(strict=True)`.

## 2. The record

- [x] 2.1 Write a test that the store lists what it holds through `opened()`, newest first, named by the question that opened each.

## 3. The API

- [x] 3.1 Write a test that a conversation's listing, turns, pin, parked card and deletion answer under `/api/conversations`.

## 4. The page

- [x] 4.1 Write a test that the rail's tab over the list reads CONVERSATIONS.
- [x] 4.2 Write a test that the start control reads "New conversation" and, refused, says the reader is already in one.
- [x] 4.3 Write a test that the delete asks with "Delete conversation".
- [x] 4.4 Write a test that the way back from a chat reads "Back to other conversations".
- [x] 4.5 Write a test that the notice for a turn landing elsewhere says CONVERSATIONS.
- [x] 4.6 Write the browser test that the CONVERSATIONS tab lists, starts and deletes a conversation under those words.

## 5. The word held out

The guard comes last: as the second item it would force the whole rename in one green step, and every test after it would pass on arrival.

- [ ] 5.1 Write a guard that no name under `src/cora` or `frontends/react` carries session, and watch it fail on `Session`.

## 6. The outer test again

Dropped after 3.1, not last: the outer test reaches the API and no further, and the new path finished it — strict xfail then failed on the pass.

- [x] 6.1 Drop the marker and watch the outer test pass.
