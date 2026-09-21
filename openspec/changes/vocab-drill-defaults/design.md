## Context

The field asks which way round before the first word, drills from SM2 whether or not
anyone wanted spacing, and speaks the language of its instructions rather than the
reader's. Three settings, asked or assumed, before a single word is put.

## Goals / Non-Goals

**Goals:**

- A session starts with no questions: German first, in German, no spacing.
- Every one of the three can be changed by asking, for the length of the conversation.
- With spacing off, a session ends, which a schedule-driven one never does.
- The schedule stays untouched while spacing is off.

**Non-Goals:**

- Detecting which column is German; the list says it by being written German first.
- Keeping any of these past the conversation, which would make a session depend on one
  weeks ago.
- Replacing SM2, which is what spacing still means when it is turned on.

## Decisions

- **The left column is German, by convention of the file** — the correction box is
  where a screenshot read the other way round is swapped, which is what settling it at
  creation means. No detection, no per-list setting, nothing to keep in step.
- **A pass is the set of words already right, not a stored order** — picking at random
  from what is left is a shuffle, and the only thing to keep is what has been done.
- **The pass lives in `cora.state`** beside the chosen list, so a conversation is a
  session and the two die together.
- **Spacing is an argument on `next_word`**, like the list and the side: one call sets
  it and the same call uses it, so there is no order to get wrong.
- **`how_it_went` writes one of two places** — the schedule with spacing on, the pass
  with it off — so nothing accumulates in a store the reader did not ask to fill.
- **Going again is an argument, not a new tool** — the finished-pass sentence says what
  to call, and the model passes it on when the reader says yes.
- **The instructions say to speak German** rather than being written in German: they
  are read by the model, and what they ask for is what the reader hears.

## Risks / Trade-offs

- **A list written English-first drills backwards**, and nothing detects it. The reader
  swaps the columns in the correction box, or asks for the other side.
- **`next_word` now takes four optional arguments**, all of them session settings; a
  second tool to set them would add an order for the model to get wrong.
- **A pass over a list of hundreds is a long session**, and nothing breaks it into
  parts. Spacing is what the reader turns on when a list gets big.
- **Randomness is real randomness**, so a test of the order is a test of a shuffle: what
  is asserted is that two passes differ, not any particular order.

## What it touches

- **Ports:** none.
- **Guards:** none new.
- **Diagrams:** none.
- **Docs:** none; the field's own instructions carry this.
