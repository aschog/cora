# Run the Telegram bot

`make bot` runs cora as a Telegram bot: the same agent, the same documents, the same
plugins as [the page](run-the-react-shell.md) — reached from a chat instead of a
browser. Install, plugins, the `.env` semantics and [the gates](get-started.md#gates)
are [get started](get-started.md). This page is what only matters here.

The bot polls Telegram, so nothing reaches into the machine cora runs on: no public
address, no inbound port, no webhook.

## The two settings

Both are read from the environment, and the bot refuses to start without either —
one line on stderr and a non-zero exit, before a model is loaded or a store is opened.

- `CORA_TELEGRAM_TOKEN` — the bot account, from Telegram's own BotFather.
- `CORA_TELEGRAM_CHATS` — the chats it answers, as ids separated by commas. Negative
  ids are groups and channels.

`make bot-env` reads them from `.env` instead, as `make run-env` is to `make run`.

There is no allowlist on Telegram's side: anyone who finds the bot can message it, and
cora would answer with your documents. So the list is required, an empty one is refused
rather than read as everybody, and a message from a chat that is not on it is dropped
without a reply — a reply is a way of saying something is there.

To find your own id, start the bot and message it: a message from a chat nobody named
is written to the terminal as the chat it came from, and none of what it said.

## What a chat can do

Ask, and read the answer with the documents it rests on named under it. The chat is the
conversation — every message runs on one thread, so what was said before is carried into
what is asked next, and two chats never read each other.

Where a turn stops to ask, the card arrives as its prompt, whatever it already holds, and
its ways off numbered. Reply with a number and the turn finishes on that choice. Reply
with anything else and it says so, leaving the turn where it was. A choice that waits on
a value somebody has to type is not offered, because a chat is not a form.

## What it does not do

Uploading a document, deleting one, managing plugins and pinning a field are the page's,
and this frontend has none of them. Answers do not stream: a turn takes as long as it
takes, and arrives whole. One message is answered at a time, so a second chat waits
behind the first.
