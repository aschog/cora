## Context

Four points let a plugin take part in a turn, and all four are on the way in — nothing
sees what cora is about to say.

## Goals / Non-Goals

**Goals** — one more point, the answer settled and not yet handed over, amendable by a
plugin and recorded on the trace like every other handler.

**Non-Goals** — reaching every model call, which the course's `after_model` does and
this deliberately does not. Reaching the model's own prose on the trace, which is
thinking rather than answer. Refusing an answer outright. Streaming, where the text has
already left before a handler could see it.

## Decisions

**A fifth entry in `EVENTS`, and nothing else in that module moves.**

- `events.py` says a new point in the turn is an entry there, and this is the change
  that tests the claim.
- The kinds — refusing and amending — are unchanged, because this needs neither a third.

**It amends rather than refuses, which is the whole design question.**

- A refusing handler raises and the turn is lost after every round it already spent.
- An amending one replaces the text, so a plugin that wants to block writes the sentence
  the reader gets instead.
- Rejected: `Refusing` — the work is done by this point, and throwing it away is a
  worse answer than a substituted one.

**It fires once, on the answer, and not on every round.**

- The rounds before the last asked for tools, and their prose is thinking rather than
  something the reader is handed as an answer.
- The honest cost: that prose is on the trace, so a plugin redacting an answer does not
  redact the trace, and the docs say so rather than implying cover it does not give.

**The answer step dispatches, because it is where the answer becomes one.**

- It already reads the last round and settles `answer`, so the handlers run between
  those two and the state holds only the amended text.
- Citations are read off `answer` after the walk, so they follow the amendment with no
  second rule.

**Streaming is what this cannot cover, and the page is what says so.**

- Text reaches the reader as it is written, so a handler seeing the settled answer sees
  it after the reader did.
- Named here rather than solved: a plugin needing it would want the model call wrapped,
  which is a bigger point than this one.

## Risks / Trade-offs

- A plugin can rewrite an answer into anything, which is the trust that loading it
  already extended.
- A redaction that leaves the trace alone can read as cover it is not, which is a
  documentation duty rather than a code one.
- Streaming means a redaction lands after the reader has seen the text, until the page
  holds the stream back for it.

## Ports, guards and diagrams

- `ANSWERING` as an added name, so `CONTRACT` stands where it is.
- No new port, no adapter, no kind of event.
- The round diagram is regenerated, because a turn gains a point.
