## Context

A document lives in the index and in a file, ingestion writes both, and nothing takes
either back — see `proposal.md` for why that is now the gap.

## Goals / Non-Goals

**Goals** — one call over both halves, a half-failed delete that leaves nothing
reachable, a name that takes every upload of it, and a page that reuses the delete it
already has.

**Non-Goals** — deleting one upload out of a name, which the rail cannot show apart.
Deleting a field. Rewriting the answers that cited the document. A record of what was
deleted, which the file itself was.

## Decisions

**The delete unwinds ingestion, in reverse.**

- `add_file` keeps the text and then indexes it, so a passage is never citable before it
  is openable; deleting drops the index and then the file.
- A delete that fails halfway then leaves a file nothing can reach — invisible, and
  overwritten by the next upload of those bytes, because `contains` is false again.
- The other order leaves the document listed, its passages silently dropped from every
  search and its citations opening onto nothing: present-looking and useless.
- Rejected: one transaction over two stores — there is none, and the order is what
  stands in for it.

**A name is every upload of it, and the index holds the mapping.**

- The rail lists what `sources` returns, which is one entry per filename however many
  uploads are behind it.
- So the retriever answers which uploads a name covers, and each is dropped from both
  stores in turn.
- Rejected: listing uploads instead of names — two identical rows, and a reader who
  cannot tell which is which.

**`KnowledgeBase` is the seam, as it already is for adding one.**

- It is the one place that knows a passage is a span in the index and a file the span
  was measured in, which is exactly what a delete has to reach.
- One call, so no frontend can drop an index and leave a file.
- Rejected: a use case beside it — a second component holding the same two ports.

**Each store gains a verb; no port is added.**

- `Documents` drops one upload's file, `Retriever` drops one upload's passages and
  answers which uploads a name covers.
- A name reaches the retriever as metadata to match and the documents store by hash, so
  neither takes a reader's string as a path.
- Rejected: a `Deletable` port over the three stores that can now forget — they share a
  shape, not a type, and one interface over them would be an abstraction with nothing
  behind it.

**The page reuses the delete it has, and adds no third of anything.**

- The row's control is the same component the other two rails draw, named for the
  document; the question is the same modal, told what to say.
- The one question slot the page already holds carries this one too.
- The row's *shape* becomes one class the three rails share; the markup stays three,
  because a document's row is a button with a cited state and a fact's row is a line of
  text — one component over both would take a parameter per difference.
- The row is disabled unless this answer cited it, so the control sits beside that
  button rather than inside it.

**What an unopenable passage says is one sentence, and it covers both cases.**

- The store cannot tell a deleted document from one whose text was never kept: both read
  as nothing.
- So the sentence is true of either, and no tombstone is written to tell them apart.
- Rejected: remembering the delete — new state in a store whose whole point is that the
  file is the record.

**What moves at the edges.**

- Ports: `documents` and `retrieval` gain methods; the map is unchanged.
- Guards and generated diagrams: none — no step, no component, no port.

## Risks / Trade-offs

- **An old answer cites what is gone** → it keeps its citation and says so on opening,
  rather than being rewritten behind the reader.
- **One name may be four documents** → the rail showed them as one, and deleting the one
  it showed is what the reader means.
- **A half-failed delete leaves a file** → unreachable, and the next upload of those
  bytes overwrites it.
- **A deleted document is uploadable again** → which is the way back from a mistake, and
  costs the parse and the embeddings.
