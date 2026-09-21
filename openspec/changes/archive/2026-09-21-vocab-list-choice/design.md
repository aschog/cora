## Context

The field's lists are its own files now, and a drill reads every one of them. A reader
with three lists gets all three shuffled together, which is not what sitting down to
practise one unit means. cora already has the shape for putting a choice: `ask_user`
stops the turn on a card of one action per option.

## Goals / Non-Goals

**Goals:**

- The reader chooses which list before the first word of a session.
- The choice is made once and holds for the rest of the conversation.
- A field with one list asks nothing.
- The model cannot skip the choice, whatever it decides to do.

**Non-Goals:**

- A card put up by the plugin itself; cora's own is the one that carries a choice back.
- Remembering the choice across conversations, which would make a session's first word
  depend on a session weeks ago.
- Choosing more than one list but not all of them.

## Decisions

- **`ask_user` is the card** — a plugin tool's `asks` can gate a call but cannot carry
  which option was taken: `_written` passes field values, and a one-field card is
  refused outright. The decision tool is the one mechanism that returns a choice.
- **The tool refuses until a choice is made**, rather than the instructions asking the
  model to be careful. A refusal naming the lists is a rule the model cannot skip and a
  sentence it can act on.
- **The choice is kept in `cora.state`** — the conversation is its life, which is what
  the story asks for and what `state` already means.
- **All of them is `*`**, which the file-name rule refuses, so no list can ever be named
  the same as the sentinel.
- **The chosen list is an argument, not a second tool** — one call sets it and the same
  call uses it, so there is no order for the model to get wrong.

## Risks / Trade-offs

- **The refusal costs a round.** The model asks for a word, is refused, puts the card.
  The alternative is instructions the model may skip, which costs a wrong session.
- **`ask_user`'s own description frames it narrowly**, as being for two readings of one
  remembered fact. The field's instructions say to use it here, and a scope's section
  is read after cora's own.
- **A renamed list drops the choice** and the next word is refused, which reads as the
  session ending oddly; naming the lists in the refusal is what gets the reader back.

## What it touches

- **Ports:** none.
- **Guards:** none new.
- **Diagrams:** none.
- **Docs:** none; the field's own instructions carry this.
