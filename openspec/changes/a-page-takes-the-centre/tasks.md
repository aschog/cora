## 1. The outer test

- [ ] 1.1 Write the functional test where fixing the conversation to a field with a page draws that page in the middle with the conversation in the rail, marked `test.fails` so the suite stays green.

## 2. Which page, if any

- [ ] 2.1 Write a test that the rails answer with the page of the field the conversation is fixed to.
- [ ] 2.2 Write a test that they answer with none where the fixed field has no page and where nothing is fixed.
- [ ] 2.3 Write a test that a field merely answered in brings no page, the pin being what fixes one.
- [ ] 2.4 Write a test that a deployment offering one field draws its page with nothing pinned.

## 3. The middle

- [ ] 3.1 Write a test that a fixed field with a page draws a frame of it, named for the field, allowing the camera and sandboxed away from nothing.
- [ ] 3.2 Write a test that a fixed field with no page draws the conversation in the middle, as before.
- [ ] 3.3 Write a test that deleting the plugin of the fixed field returns the conversation to the middle as the reader confirms it.

## 4. The conversation in the rail

- [ ] 4.1 Write a test that with a page drawn the conversation is inside the rail and not in the middle.
- [ ] 4.2 Write a test that its composer takes a question there and the answer lands in it.
- [ ] 4.3 Write a test that a turn moving the panels to the steps leaves the conversation drawn.
- [ ] 4.4 Write a test that choosing another panel leaves the conversation drawn and unchanged.
- [ ] 4.5 Write a test that a panel that throws is a sentence in its own place and the conversation stands.
- [ ] 4.6 Write a test that a conversation that throws in the rail is a sentence in its place, and the panels and the page stand.
- [ ] 4.7 Write a test that what was typed and not yet asked survives a move between panels.
- [ ] 4.8 Write a test that the conversation in the rail is headed by the question that opened it.
- [ ] 4.9 Write a test that a conversation nothing has been asked in is headed as a new one.

## 5. Room for the page

- [ ] 5.1 Write a test that folding the rail beside a page and unfolding it draws the conversation with its turns still there.

## 6. What the page is, to a reader

- [ ] 6.1 Write a test that the region the screen is about holds the page where one is drawn and the conversation where none is.
- [ ] 6.2 Write a test that the conversation in the rail is a region named for itself, inside no second main.

## 7. Through the browser

- [ ] 7.1 Write a browser test that a fixture plugin bringing a page has it drawn when its field is fixed, answers a question in the rail beside it, and keeps its composer reachable at the rail's own width.

## 8. Close it

- [ ] 8.1 Drop the outer test's marker and watch it pass.
