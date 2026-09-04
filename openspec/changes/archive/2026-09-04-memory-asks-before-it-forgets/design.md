## Context

Deleting a conversation asks first and forgetting a fact does not, so one rail is
careful and the rail beside it is not.

## Goals / Non-Goals

**Goals** — one question shape over both rails, one control shape over both rows, and a
rail where nothing destructive is drawn in the palette's warm pair.

**Non-Goals** — undoing a forget, which no store here can offer. Asking twice for the
same fact. What cora remembers and when, which no part of this touches. The sessions
rail, which asks already.

## Decisions

**The question generalises rather than multiplying.**

- The modal the sessions rail raised becomes one that is told what to say: what kind of
  question it is, what is going, what is lost and what going ahead is called.
- Three callers then, one component — the alternative is a second modal saying the same
  thing about a different noun.
- Rejected: one modal per rail — the second would drift from the first in wording,
  spacing and the ways out of it.

**The page holds one question at a time, and what to do about it.**

- One slot in the page's state, carrying the words and the act, because one question
  stands over the page at a time.
- The act runs after the question closes, so a failure it reports is not cleared by the
  card coming down.
- Rejected: a slot per rail — three states and three render sites for one overlay.

**Forgetting everything is the same question about a different subject.**

- It names every fact rather than one, and says the documents and the conversations
  stay.
- Rejected: leaving it unasked — it is the most destructive control in either rail.

**The fact's row becomes the conversation's row.**

- The same control component, named for the fact instead of the conversation.
- `.destructive` and the card the facts sat in go, and magenta loses its last
  destructive job: the palette note says so.
- Rejected: keeping the word `forget` beside the icon — the icon's name is the fact,
  and a word repeated down the rail is the noise the sessions rail already dropped.

**What moves at the edges.**

- No port, no endpoint, no payload: the two requests behind this already exist.
- Guards and generated diagrams: none — nothing here is a step, a component or a port.

## Risks / Trade-offs

- **A question for something cheap to say again** → a fact is cheap to say and the rail
  cannot say which are, and the reader who wanted it gone still gets it gone.
- **Two clicks to forget one fact** → the second is the one that means it, and the rail
  is not a place readers spend their day.
- **One modal serving two rails** → it is told every word it says, so neither rail can
  put the other's wording on the page.
