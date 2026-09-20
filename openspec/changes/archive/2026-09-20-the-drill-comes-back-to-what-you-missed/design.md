## Context

The field holds lists as documents and drills by improvising over them. A plugin now has
a store of its own. See proposal.md — Why.

## Goals / Non-Goals

**Goals** — spacing that survives the conversation, and a drill the model runs through
tools rather than from what it can see.

**Non-Goals** — a page, a picker, statistics, and anything about how a hint is worded,
which the instructions already say.

## Decisions

**SM-2, and not FSRS.**

- Wozniak's SM-2 is an interval and an ease per word, and it is the published baseline
  every flashcard program still runs — twenty lines of arithmetic against a model with
  seventeen parameters and a trainer.
- Rejected: a Leitner box, which is SM-2 with the ease taken out and the same code.

**The schedule is JSON in the plugin's own store, one name.**

- It is the plugin's own bookkeeping: not searched, not cited, not the reader's to edit,
  which is exactly what the store is for and what a document is not.
- One name for the whole schedule rather than one per word: it is read whole to pick a
  word anyway, and a hundred words is a small file.

**The pairs are read out of the documents each time.**

- The lists are the reader's and they change: a schedule that also held the words would
  answer from a copy of a list that has since been edited.
- A word is keyed by the two sides it joins, so an edited list drops what it dropped.

**Two tools, and the model drives them.**

- `next_word` picks and puts; `how_it_went` moves the schedule. The model does the
  talking, the hint and the marking, and the arithmetic is not its to do — the same
  rule the fitness field already holds for its calculators.
- What was last asked is conversation state, not schedule: it is the turn's business
  and goes with the conversation.

## Risks / Trade-offs

- The model could mark a word without asking it → the instructions say when to call,
  and a miscall costs one word's schedule rather than the file.
- A list edited between sessions orphans a word's entry → it is dropped on the next
  read, which is what keying by the pair buys.
- Two conversations drilling at once → last write wins, as everywhere else a plugin
  keeps something.

## Ports, guards and diagrams

- No port and no core change: this is the plugin over the store the core now offers.
- No guard changes and no diagram changes: nothing about the composition moves.
