# What cora does

The behaviour you meet. Why a turn runs that way is
[what happens when you ask](happy-path.md); where any of it is kept is
[where your data lives](data-storage.md).

## Fields

- A field comes with the plugin that registers it, or is named by a deployment — which
  is how a field holding only documents exists.
- Every question is answered in exactly one, and a search sees that field and no other.
- On *Chat*, cora routes each question and says which field on the trace, stopping to
  ask when one fits two.
- Pick a field under *+ Plugin* and every later turn is answered in it. A pin is set
  once: a second field is a second conversation.

## Cards

- One shape over every stop: a fork between two remembered values, a question about
  which field the turn belongs to, a call about to change something outside cora, and a
  form to fill in.
- A field carries the JSON Schema it came from, so a plugin's card needs no change to
  the page.
- A card whose required fields are empty cannot be sent.
- A card is for two values or more. One is asked for in a sentence you answer in the
  composer; none at all still stands — a yes, or a confirmation.

## Deleting what it holds

- Each rail deletes one thing at a time, asks first, and says what is lost *and* what is
  not.
- A conversation goes as its turns and the thread they ran on; a document as its
  passages and the file its citations opened onto; a plugin as every field only it
  brought, with those documents and the conversations pinned there.
- What cora remembers about you, and whatever an approved effect wrote, are never taken.

## Effects, and the gate they wait at

- A tool declaring it changes something outside cora stops the turn: you see the call
  and the arguments the model wrote, and nothing happens until you approve.
- Decline and nothing outside cora changed, the model is told, and the turn still
  answers.
- The gate is a step of the core on the only path from the model to its tools: no plugin
  can switch it off, subscribe to it, or reach a tool around it, and no handler may pause
  a turn. It covers every tool a plugin declared. A plugin's own card can *look* like the
  gate's, though — cora draws every card with one component — so what says the gate ran
  is the trace.

## What a plugin keeps

What a plugin keeps under a name of its own is there next turn, rides the same
checkpoint, and goes when the conversation does. That is not what cora remembers, which
is about *you* and outlives every conversation.
