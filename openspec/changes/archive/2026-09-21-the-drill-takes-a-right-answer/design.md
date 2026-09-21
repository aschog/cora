## Context

The drill's two tools are called by the model on every answer: it judges what the reader
typed, records it, and asks for the next word. The pass is held in memory, the lists are
read off the field's files, and the session's settings are in the plugin's state — bound
inside a tool call, and, since `a-plugin-takes-the-question`, inside a taking handler.

## Goals / Non-Goals

**Goals:**

- A right answer is a lookup and a pop, not a round.
- The model stays the judge of everything that is not letter-for-letter right.
- The pass, the schedule and the check on the answer are untouched.

**Non-Goals:**

- Judging a near miss locally — an article, a typo; the model does that, as today.
- Taking a spaced session locally; what is due next is the model's call for now.
- Closing a pass locally; it ends in a question, and questions are the model's.

## Decisions

- **The handler calls the two tools rather than the pass.** Taking is `how_it_went`
  then `next_word`, as the model would call them, under the same bound state — so a
  word is recorded one way and the next is put one way, whoever asked.
- **Right is the other side, case folded, closing punctuation dropped, and no looser.**
  Anything looser is a judgement, and judging is what the model is for. Strictness costs
  a round on `the dog`; looseness would cost a wrong right.
- **A hint is read off the turn, not off the text.** The drill cannot see a hint, but it
  can see that the model was asked while the word stayed on the table. The flag is set
  when the handler passes a question on and cleared when the word is answered, and a
  right answer under it is recorded as missed — which is what the instructions promise.
- **The last word and a spaced session go to the model.** Both end in something to say:
  a pass done, an offer to go again, nothing due. Saying is the model's.
- **The instructions say what changed.** The model now reads a transcript it did not
  write; told so, it takes the last word put as the word on the table.

## Risks / Trade-offs

- **A right answer after a question that was not a hint counts as missed** → the word
  comes round once more; a minute of practice, and no wrong is recorded for good.
- **An answer the model would have judged right costs a round** → as today, and no worse.
- **The pass is one per process, so the handler shares its ceiling** → unchanged, and
  marked where the pass is.

## What it touches

- **Ports:** none.
- **Guards:** none new.
- **Diagrams:** none.
- **Docs:** none; the field's own instructions carry this.
