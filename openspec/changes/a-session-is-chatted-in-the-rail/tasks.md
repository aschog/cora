## 1. The outer test

- [ ] 1.1 Write the functional test where a conversation fixed to a field with a page is chatted in the rail, the way back shows the list, and opening another from it chats that one, marked `test.fails`.

## 2. What a listed conversation says

- [ ] 2.1 Write a test that the sessions listing carries the field each conversation is fixed to.
- [ ] 2.2 Write a test that a conversation fixed to nothing is listed with none.

## 3. The list

- [ ] 3.1 Write a test that a conversation fixed to a field with a page is marked and the others are not.
- [ ] 3.2 Write a test that the list says what the mark means.
- [ ] 3.3 Write a test that the mark follows the page rather than the pin alone, so a field with no page is unmarked.

## 4. The chat

- [ ] 4.1 Write a test that a conversation fixed to a field with a page is the sessions panel, filling the rail.
- [ ] 4.2 Write a test that its head carries the question that opened it, its field and how many turns it holds.
- [ ] 4.3 Write a test that a conversation nothing has been asked in is headed as a new one.
- [ ] 4.4 Write a test that the way back draws the list in its place.
- [ ] 4.5 Write a test that opening a marked conversation from the list chats it.
- [ ] 4.6 Write a test that the middle still holds the page throughout.

## 5. What stays where it was

- [ ] 5.1 Write a test that a conversation fixed to nothing is drawn in the middle and the rail is the list.
- [ ] 5.2 Write a test that opening an unmarked conversation from the list returns the conversation to the middle.
- [ ] 5.3 Write a test that a panel that throws is a sentence in its place and the page still stands.

## 6. Asking in the rail

- [ ] 6.1 Write a test that a turn asked in the rail leaves the panels on the sessions tab.
- [ ] 6.2 Write a test that the question and the answer land in the chat.
- [ ] 6.3 Write a test that a turn asked from the middle still moves the panels to the steps.

## 7. Through the browser

- [ ] 7.1 Write a browser test that a fixed field's page is drawn, its conversation is chatted in the rail, the way back lists the others, and a question asked there is answered there.

## 8. Close it

- [ ] 8.1 Drop the outer test's marker and watch it pass.
