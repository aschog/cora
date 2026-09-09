# What cora does

The behaviour you meet. How a turn runs is
[what happens when you ask](happy-path.md); where any of it is kept is
[where your data lives](data-storage.md).

## Fields

A field comes with the plugin that registers it, or is named by a deployment — which is
how a field holding only documents exists. Every question is answered in exactly one,
and a search sees that field and no other.

On *Chat*, cora reads each question into the field it belongs to, says which on the
trace, and stops to ask when one fits two. Pick a field under *+ Plugin* and every later
turn is answered in it, through a reload and a reopen. A pin is set once: a second field
is a second conversation.

## Cards

Everything cora stops for is one card — a question between two remembered weights, a
call about to change something outside cora, a form to fill in. Each field carries the
JSON Schema it came from, so a plugin adds a card the page has never seen: the card is
data cora sends, not code anybody shipped.

- Cora asks for what it lacks as one of those, naming the fields itself rather than
  asking one question at a time. A deployment with no plugin loaded asks this way too.
- A card whose required fields are empty cannot be sent.
- A card is for two values or more. Where one is all that is missing, cora asks in a
  sentence and you answer in the composer.
- A card asking for *none* still stands: a call waiting on your yes, or what a tool
  worked out put up to be confirmed.

## Deleting what it holds

Each rail deletes one thing at a time, asks first, and says what is lost *and* what is
not.

- **A conversation** goes as both halves: the turns, and the thread they were answered
  on. The one you are reading offers no delete, and neither does one still answering.
- **A fact** the same way — and forgetting everything is asked about too.
- **A document** goes as its passages and the file its citations opened onto. The same
  file in another field is left alone. Answers keep their citations and say the document
  is gone; upload it again and it is indexed again.
- **A plugin** takes every field only it brought, with those documents and every
  conversation pinned there. What cora remembers, and what an approved effect wrote,
  are left. A symlink is unlinked and its target untouched.

## Effects, and the gate they wait at

A tool that declares it changes something outside cora does not run on the model's word.
The turn stops, the page shows the call and the arguments the model wrote, and nothing
happens until you approve. Decline and nothing outside cora changed, the model is told,
and the turn still answers.

- A round proposing two effects stops twice and settles both before either runs, so
  picking the turn up replays neither.
- The gate is a step of the core on the only path from the model to its tools: no plugin
  can switch it off or imitate it, because no handler may stop a turn.
- It covers what was declared. What a plugin's own code does inside a call it was
  allowed to make is the trust you extended by loading it.

## What a plugin keeps

What a plugin puts under a name of its own is there next turn, rides the same checkpoint,
and goes when the conversation does — a plan it is revising, a form half filled in. That
is not what cora remembers, which is about *you* and outlives every conversation. A
plugin's own loop says what it did on the trace, in a line cora signs with its name.
