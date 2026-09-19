## Context

The API lists a field's names and opens an upload by its hash, and only a citation hands
the page a hash. See proposal.md — Why.

## Goals / Non-Goals

**Goals** — a page reads what it saved into its field, by the name the listing shows.

**Non-Goals** — a search, a rename, a change to the listing, or a page using the route.

## Decisions

**The knowledge base answers, the route relays.**

- The knowledge base already maps a name to its uploads and an upload to its text, for
  `all` and for the delete; one more method reads one name that way.
- The route composes nothing itself, as the other routes compose nothing.
- Rejected: the route calling the retriever and the store, because no route does.

**Read on the path the delete takes.**

- `GET` where `DELETE` already stands, so one path names one document either way.
- Rejected: a query on the listing, which would bloat the rail's call for every row.

**Every upload, oldest first.**

- Two uploads of one name are two documents, as `all` and the delete already hold.
- Rejected: the newest only, which would hide a document the rail counts.

**Not there is a sentence, refused is the listing's refusal.**

- An empty answer for a name is a 404 with a sentence, as the read by upload answers.
- A field nobody loaded is refused by the same helper every field-taking route uses.

## Risks / Trade-offs

- A name with many uploads returns every text at once — a field's documents are few.
- The text is the cleaned text the field kept, not the bytes uploaded, as citations read.

## Ports, guards and diagrams

- No port changes: the retriever and the store already offer what is composed.
- No guard and no diagram is touched.
