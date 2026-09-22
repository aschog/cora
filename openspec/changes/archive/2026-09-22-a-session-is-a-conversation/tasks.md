## 1. The outer test

- [x] 1.1 Write the outer test, marked `xfail(strict=True)`: one answered conversation is listed and read back at `/api/conversations`, and `/api/sessions` answers nothing.

## 2. The record

- [x] 2.1 Write a test that `opened()` lists the store's conversations newest first, each named by its opening question.

## 3. The API

- [x] 3.1 Write a test that a conversation's listing, turns, pin, parked card and deletion answer under `/api/conversations`.

## 4. The page

- [x] 4.1 Write a test that the rail's tab over the list reads CONVERSATIONS.
- [x] 4.2 Write a test that the start control reads "New conversation", and refuses by saying the reader is in one.
- [x] 4.3 Write a test that the delete asks with "Delete conversation".
- [x] 4.4 Write a test that the way back from a chat reads "Back to other conversations".
- [x] 4.5 Write a test that the notice for a turn landing elsewhere says CONVERSATIONS.
- [x] 4.6 Write the browser test that the CONVERSATIONS tab lists, starts and deletes a conversation under those words.

## 5. The word held out

The guard comes last, since as the second item it would force the whole rename into one green step.

- [x] 5.1 Write a guard that nothing under `src/cora` or `frontends/react` names a session, and watch it fail on `Session`.

## 6. The outer test again

Dropped after 3.1 rather than last, because the outer test reaches only the API and the new path finished it.

- [x] 6.1 Drop the marker and watch the outer test pass.
