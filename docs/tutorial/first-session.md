# Your first session

Half an hour, one document, and a model you pay for by the token. By the end you will
have uploaded a document, had it answered from, followed a citation back to the passage
it came from, and asked cora to remember something about you.

You need what [get started](../how-to/get-started.md) lists, and an
[OpenRouter key](https://openrouter.ai/keys).

## 1. Install

--8<-- "docs/how-to/get-started.md:install"

## 2. Start it with plugins

--8<-- "docs/how-to/get-started.md:run"

Your key goes in the first line — [openrouter.ai/keys](https://openrouter.ai/keys).

The second line is what turns this from a bare cora into a coach and a travel companion
with a prompt-injection screen. Drop it to see what the box does on its own.

## 3. Pick a field, or let cora pick

Leave the strip above the conversation on *Chat* and cora reads each question into the
field it belongs to. If yours is about one of them, pick it under *+ Plugin* — every
later turn is answered in it. Why it works that way:
[what cora does](../what-it-does.md#fields).

Give travel something to answer from by uploading the notes it ships, in
`plugins/travel/src/cora/plugins/travel/corpus/` — with `travel` picked under
*+ Plugin*, because a field answers from its own documents and no others. Picking it
here pins the conversation, so do this in one you are willing to keep in travel.

## 4. Ask it something

Upload a document (txt/md/pdf) in the documents rail on the left. It lands in the field
the conversation is running in — whichever *+ Plugin* is showing, or the one beside
*YOUR DOCUMENTS* while that says *Chat* — and the rail lists that field's documents. A
turn answers from the field it runs in, so a document put in the other one is a document
it will not find. Then ask about it: answers cite the passages they used. Click
a `[1]` in an answer and that document opens with the cited passage highlighted, read
back out of the Markdown file cora kept it as. The steps appear as cora takes them,
under the *STEPS* tab on the right: what it decided, which tool it ran and what came
back. A
question that needs no documents is answered without searching them.

Ask it to remember something — "remember that I train on Tuesdays and Thursdays",
"I'm vegetarian, keep that in mind" — and it keeps that between sessions: the *MEMORY*
tab lists every fact it holds, forgets one at a time, or forgets everything. It only remembers when you ask it to, never on its own judgement,
and each save appears in the trace.

## Where to go next

- [What happens when you ask](../happy-path.md) — the same session as sequence diagrams,
  read out of the code that runs it
- [What it is made of](../big-picture.md) — why cora is built this way
- [Write a plugin](../how-to/write-a-plugin.md) — your own domain instead of the coach
