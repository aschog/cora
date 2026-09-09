# Your first session

By the end you will have uploaded a document, had it answered from, followed a citation
back to the passage it came from, and asked cora to remember something about you.

You need what [get started](../how-to/get-started.md) lists, and an
[OpenRouter key](https://openrouter.ai/keys).

## 1. Install

--8<-- "docs/how-to/get-started.md:install"

## 2. Load the plugins

--8<-- "docs/how-to/get-started.md:plugins"

That is what makes this a coach and a travel companion rather than a bare cora, with a
prompt-injection screen over both.

## 3. Start it

--8<-- "docs/how-to/get-started.md:run"

Your key goes in the first line — [openrouter.ai/keys](https://openrouter.ai/keys).

## 4. Pick a field, or let cora pick

Leave the strip above the conversation on *Chat* and each question is answered in the
field it belongs to. Pick one under *+ Plugin* and every later turn is answered in it —
a pin is set once, so use a conversation you are willing to keep there.
[Why](../what-it-does.md#fields).

## 5. Ask it something

1. Pick `travel` under *+ Plugin*.
2. Upload a note in the rail on the left. An upload lands in the field the conversation is running in, and a turn answers from that field only.
3. Ask about it. The answer cites what it used — click a `[1]` and the document opens at
   the passage. *STEPS*, on the right, is what cora did to get there.
4. Say "remember that I train on Tuesdays and Thursdays". It keeps that between
   sessions, and only ever when you ask: *MEMORY* lists what it holds and forgets it.

## Where to go next

- [What happens when you ask](../happy-path.md) — the same session as sequence diagrams,
  read out of the code that runs it
- [What it is made of](../big-picture.md) — why cora is built this way
- [Write a plugin](../how-to/write-a-plugin.md) — your own domain instead of the coach
