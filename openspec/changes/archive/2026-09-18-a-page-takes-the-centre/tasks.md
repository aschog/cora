## 1. The outer test

- [x] 1.1 Write the functional test where fixing the conversation to a field with a page draws that page in the middle with the conversation in the rail, marked `test.fails` so the suite stays green.

## 2. Which page, if any

- [x] 2.1 Write a test that the rails answer with the page of the field the conversation is fixed to.
- [x] 2.2 Write a test that they answer with none where the fixed field has no page and where nothing is fixed.
- [x] 2.3 Write a test that a field merely answered in brings no page, the pin being what fixes one.
- [x] 2.4 Write a test that a deployment offering one field draws its page with nothing pinned.

## 3. The middle

- [x] 3.1 Write a test that a fixed field with a page draws a frame of it, named for the field, allowing the camera and sandboxed away from nothing.
- [x] 3.2 Write a test that a fixed field with no page draws the conversation in the middle, as before.
- [x] 3.3 Write a test that deleting the plugin of the fixed field returns the conversation to the middle as the reader confirms it.

## 4. The conversation in the rail

- [x] 4.1 Write a test that with a page drawn the conversation is inside the rail and not in the middle.
- [x] 4.2 Write a test that its composer takes a question there and the answer lands in it.
- [x] 4.3 Write a test that a turn moving the panels to the steps leaves the conversation drawn.
- [x] 4.4 Write a test that choosing another panel leaves the conversation drawn and unchanged.
- [x] 4.5 Write a test that a panel that throws is a sentence in its own place and the conversation stands.
- [x] 4.6 ~~A conversation that throws in the rail is a sentence in its place.~~ Dropped: nothing outside the conversation can make it throw while rendering — a malformed turn is caught before it is drawn — so the boundary it keeps is written from the rule and not from a test.
- [x] 4.7 Write a test that what was typed and not yet asked survives a move between panels.
- [x] 4.8 Write a test that the conversation in the rail is headed by the question that opened it.
- [x] 4.9 Write a test that a conversation nothing has been asked in is headed as a new one.

## 5. Room for the page

- [x] 5.1 Write a test that folding the rail beside a page and unfolding it draws the conversation with its turns still there.

## 6. What the page is, to a reader

- [x] 6.1 Write a test that the region the screen is about holds the page where one is drawn and the conversation where none is.
- [x] 6.2 Write a test that the conversation in the rail is a region named for itself, inside no second main.

## 7. Through the browser

- [x] 7.1 Write a browser test that a fixture plugin bringing a page has it drawn when its field is fixed, answers a question in the rail beside it, and keeps its composer reachable at the rail's own width.
- [x] 7.2 Write a browser test that a document far taller than the rail leaves both the panel and the conversation usable, the composer inside the rail.
- [x] 7.3 Write a test that a field a turn was answered in, which the deployment no longer offers, is not where the rail sits.

## 8. Close it

- [x] 8.1 Drop the outer test's marker and watch it pass.
