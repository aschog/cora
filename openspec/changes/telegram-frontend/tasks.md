# Tasks

Every item is one failing test, driven through the frontend's own surface with a
hand-written fake of the Bot API — the network is the one boundary that gets stubbed.

Section 7 is the transport read against the real Bot API, and was not on the list when
it was written. Section 10 is the review, whose findings are tests here rather than
notes somewhere.

## 1. The story, end to end

- [x] 1.1 Write the outer test, `xfail(strict=True)`: an allowed chat asks a question
      about an indexed document, and the answer is sent back to that chat.

## 2. Only the chats named are answered

- [x] 2.1 Write a test that a message from a chat the deployment names is answered.
- [x] 2.2 Write a test that a message from a chat it does not name is answered with
      nothing sent, and no turn run.
- [x] 2.3 Write a test that a message from an unnamed chat still advances the poll, so
      the next allowed message is read.
- [x] 2.4 Write a test that a deployment naming no chat refuses to start, saying so.
- [x] 2.5 Write a test that a deployment holding no bot token refuses to start, saying
      which is missing.
- [x] 2.6 Write a test that an unnamed chat is named in the log by its id and by nothing
      it said, which is where an operator finds the number to allow.
- [x] 2.7 Write a test that the chats are read as the ids they are, a group's negative
      one included.
- [x] 2.8 Write a test that a chat that is not an id refuses the start rather than
      answering nobody.
- [x] 2.9 Write a test that a blank token is no token.

## 3. A chat is a conversation

- [x] 3.1 Write a test that two questions from one chat run on one thread, the second
      carrying the first in its history.
- [x] 3.2 Write a test that two chats run on threads of their own, neither carrying what
      the other said.

## 4. What a turn came back with, rendered

- [x] 4.1 Write a test that an answer is rendered as the text the turn wrote.
- [x] 4.2 Write a test that the documents an answer cites are named under it.
- [x] 4.3 Write a test that an answer citing nothing is sent with no sources under it.
- [x] 4.4 Write a test that an answer past Telegram's message ceiling is sent in parts,
      whole.
- [x] 4.5 Write a test that a part is cut at a line rather than mid-word.

## 5. A card in the chat

- [x] 5.1 Write a test that a paused turn sends the card's prompt with its ways off
      numbered.
- [x] 5.2 Write a test that a reply naming one of those numbers finishes the turn on that
      action.
- [x] 5.3 Write a test that a reply naming no way off is told what the card expects, and
      leaves the turn parked.
- [x] 5.4 Write a test that an action waiting on a value the chat cannot write is not
      among the numbers offered.
- [x] 5.5 Write a test that a card's values travel back unchanged when a way off is
      taken.
- [x] 5.6 Write a test that a bot started while a chat is parked reads the open card off
      the agent, having held nothing itself.
- [x] 5.7 Write a test that a reply naming no number at all settles nothing.
- [x] 5.8 Write a test that an effect is approved from the chat, with the arguments it
      would run on laid out above the yes.

## 6. When a turn fails

- [x] 6.1 Write a test that a question a rule refuses is reported to the chat in cora's
      own words.
- [x] 6.2 Write a test that a failure cora modelled is reported in its own words.
- [x] 6.3 Write a test that a failure cora does not model is reported as one sentence
      carrying nothing of it, and is on the log whole.
- [x] 6.4 Write a test that the chat whose turn just failed is answered when it asks
      again.

## 7. The Bot API as it really answers

- [x] 7.1 Write a test that a text message arrives as the chat and the text it carried.
- [x] 7.2 Write a test that an update carrying no text — a sticker, an edit — is skipped
      rather than answered.
- [x] 7.3 Write a test that an update is acknowledged, so it is never read twice.
- [x] 7.4 Write a test that a poll that drops is waited out and asked again.
- [x] 7.5 Write a test that a call refused for any other reason is not swallowed.
- [x] 7.6 Write a test that the token is not in what a refused call raises.
- [x] 7.7 Write a test that a chat which blocked the bot does not end the bot.
- [x] 7.8 Write a test that a send refused for any other reason is raised.
- [x] 7.9 Write a test that nothing is sent for nothing to say.
- [x] 7.10 Write a test that being asked to wait is waited out and the call made again.
- [x] 7.11 Write a test that the client reads for longer than the poll is held open.
- [x] 7.12 Write a test that only the updates the bot answers are asked for.
- [x] 7.13 Write a test that an answer is sent to the chat it was asked in.

## 8. The workspace sees a second frontend

- [x] 8.1 Write a guard that every frontend the workspace ships is named by a documented
      command that starts it.
- [x] 8.2 Write a guard that the component map draws every frontend the workspace ships,
      so a stale drawing is a red test.

## 9. The outer test

- [x] 9.1 Drop the `xfail` marker from 1.1 and watch it pass.

## 10. What the review found

- [x] 10.1 Write a test that a plugin dropped between two messages is in the second
      turn, which is the composition the shipped command really hands the loop.
- [x] 10.2 Write a test that a plugin the folder cannot load costs one message rather
      than the bot.
- [x] 10.3 Write a test that a reply whose connection drops does not end the bot.
- [x] 10.4 Write a test that a rate outlasting one wait is waited out again.
- [x] 10.5 Write a test that a rate outlasting every wait still does not end the bot.
- [x] 10.6 Write a test that a wait longer than the ceiling is capped.
- [x] 10.7 Write a test that a wait asked for in something other than JSON is still
      waited out.
- [x] 10.8 Write a test that the client carrying the token in its URLs does not log
      them.
- [x] 10.9 Write a test that a part is cut at a word where the answer has no lines.
- [x] 10.10 Write a test that an answer with nowhere to cut is still cut.
- [x] 10.11 Write a test that the ceiling counts what Telegram counts, in emoji.
- [x] 10.12 Write a test that an answer opening with a line break sends no blank part.
- [x] 10.13 Write a test that a reply of a digit `int` refuses to read settles nothing.
- [x] 10.14 Write a test that names the chat each answer was delivered to, not only the
      thread it ran on.
