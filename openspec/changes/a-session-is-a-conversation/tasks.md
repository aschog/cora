## 1. The outer test

- [ ] 1.1 Write the outer test: a conversation answered once is listed at `/api/conversations` and read back from there, and `/api/sessions` answers nothing, marked `xfail(strict=True)`.

## 2. The word held out

- [ ] 2.1 Write a guard that no name under `src/cora` or `frontends/react` carries session, and watch it fail on `Session`.

## 3. The record

- [ ] 3.1 Write a test that the store lists what it holds through `opened()`, newest first, named by the question that opened each.

## 4. The API

- [ ] 4.1 Write a test that a conversation's listing, turns, pin, parked card and deletion answer under `/api/conversations`.

## 5. The page

- [ ] 5.1 Write a test that the rail's tab over the list reads CONVERSATIONS.
- [ ] 5.2 Write a test that the start control reads "New conversation" and, refused, says the reader is already in one.
- [ ] 5.3 Write a test that the delete asks with "Delete conversation".
- [ ] 5.4 Write a test that the way back from a chat reads "Back to other conversations".
- [ ] 5.5 Write a test that the notice for a turn landing elsewhere says CONVERSATIONS.
- [ ] 5.6 Write the browser test that the CONVERSATIONS tab lists, starts and deletes a conversation under those words.

## 6. The outer test again

- [ ] 6.1 Drop the marker and watch the outer test pass.
