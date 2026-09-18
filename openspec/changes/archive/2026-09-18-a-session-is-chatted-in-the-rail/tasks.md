## 1. The outer test

- [x] 1.1 Write the functional test where a conversation fixed to a field with a page is chatted in the rail, the way back shows the list, and opening another from it chats that one, marked `test.fails`.

## 2. What a listed conversation says

- [x] 2.1 Write a test that the sessions listing carries the field each conversation is fixed to.
- [x] 2.2 Write a test that a conversation fixed to nothing is listed with none.

## 3. The list

- [x] 3.1 Write a test that a conversation fixed to a field with a page is marked and the others are not.
- [x] 3.2 Write a test that the list says what the mark means.
- [x] 3.3 Write a test that the mark follows the page rather than the pin alone, so a field with no page is unmarked.

## 4. The chat

- [x] 4.1 Write a test that a conversation fixed to a field with a page is the sessions panel, filling the rail.
- [x] 4.2 Write a test that its head carries the question that opened it, its field and how many turns it holds.
- [x] 4.3 Write a test that a conversation nothing has been asked in is headed as a new one.
- [x] 4.4 Write a test that the way back draws the list in its place.
- [x] 4.5 Write a test that opening a marked conversation from the list chats it.
- [x] 4.6 Write a test that the middle still holds the page throughout.

## 5. What stays where it was

- [x] 5.1 Write a test that a conversation fixed to nothing is drawn in the middle and the rail is the list.
- [x] 5.2 Write a test that opening an unmarked conversation from the list returns the conversation to the middle.
- [x] 5.3 Write a test that a panel that throws is a sentence in its place and the page still stands.

## 6. Asking in the rail

- [x] 6.1 Write a test that a turn asked in the rail leaves the panels on the sessions tab.
- [x] 6.2 Write a test that the question and the answer land in the chat.
- [x] 6.3 Write a test that a turn asked from the middle still moves the panels to the steps.

## 7. Through the browser

- [x] 7.1 Write a browser test that a fixed field's page is drawn, its conversation is chatted in the rail, the way back lists the others, and a question asked there is answered there.

## 8. Found in use

- [x] 8.1 Write a test that the rail names the field once, in the head of the chat.
- [x] 8.2 Write a test that a pinned conversation in the middle still says which field it is in.

## 9. Close it

- [x] 9.1 Drop the outer test's marker and watch it pass.
