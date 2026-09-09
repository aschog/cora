# Where your data lives

Everything cora keeps is on your own machine, in two shapes. What cora keeps for
itself is one SQLite file. What you can read yourself is kept beside it as files: the
text of your documents, and whatever an approved effect wrote. Which paths those are,
and which variable moves each, is the table on
[privacy, and what a plugin costs](privacy-and-ethics.md#what-is-kept-and-where) —
this page is about how the two shapes work.

## One file, four writers

`.cora/cora.sqlite` holds four stores that never had a reason to be four files. A
deployment moves all of it by naming one path, a backup is one file, and deleting it
starts a clean cora rather than a cora missing one of its halves. Each store owns its
own tables and opens its own connection through `src/cora/adapters/sqlite_store.py`,
which sets the two things four writers need: write-ahead logging, so a write does not
lock out every reader the page has, and autocommit, so a store that wants a transaction
opens one itself. A contended writer waits the five seconds `sqlite3` already installs.

Nothing migrates. Every table is created by the first writer that needs it, with
`create table if not exists`, so a fresh file and a file that has been in use since the
first release are the same file.

**The passages.** `cora_passages` is one row per chunk — the field it was uploaded
into, the filename it came from, its position in that document, and the offset and
length of its span. Not its text: the words are read back out of the Markdown file when
the passage is retrieved, so the text of a document exists once. `cora_vectors` beside
it is a `sqlite-vec` virtual table keyed by the same row id, cosine distance, with the
field as `vec0`'s partition key rather than a `where` clause — a field's vectors sit
apart, so a leak between fields is not one missing clause away. The table is created by
the first write, at the width of the vector it is handed, and the file then keeps that
width: an embedder of another size cannot be indexed into a store that already holds
one, and the way out is deleting the store and uploading again, which a changed embedder
needs anyway.

**The facts.** What you asked cora to remember is LangGraph's own store, under a
namespace of cora's — `memories`, then the user, which is `local`. A fact's key is a
nanosecond ordinal with a random tail, because the store stamps its own timestamps to
the second and two facts remembered in one breath would tie. Ordering is what the key is
for.

**The turns.** `cora_turns` is one row per turn, in the order the turns were taken —
the row id is what "in order" and "the newest conversation" both read off, so neither
depends on a clock. The row carries the question, the answer, the citations, the fields
it ran in, and the trace, as JSON. The trace nests, so each step is written tagged with
its kind and its own steps written the same way, which is what lets a step of a
delegated loop read back as the kind it was rather than a bare dictionary.

**The checkpoints.** LangGraph's saver, in the same file, holding the state of every
thread: the brief the model was given, the transcript, the tool results it was shown,
whatever a plugin kept under its own names, the pin, and any card the turn stopped on.
This is the half that makes a reload work — a turn parked on a question is a checkpoint
waiting to be picked up. It sits beside the turns deliberately: what the model was told
and what the page redraws are two halves of one conversation, and a deployment deleting
the file should lose both or neither.

## The documents are files you can open

`.cora/documents` is a directory per field, and one Markdown file per upload under it —
`travel` holds `kyoto-8f21c0a4e9d3.md`. The file holds the cleaned text and nothing else,
because a citation's offsets are positions in it. The name is the upload's filename plus
the head of the sha256 of the bytes it arrived as, which does two things — the same
filename uploaded twice is two files rather than one overwritten, and the store is its
own index, needing no table to say which file an upload is. The full hash is what names
an upload everywhere else, and the head only narrows the search for it, so a short name
is never something a request can talk cora into reading.

A field is a directory here, so its name is checked against a bare-name pattern before a
byte is written — a field called `../..` is refused rather than resolved.

It is a directory rather than a table for one reason: you can open it and read what cora
has.

## What an effect wrote is not cora's

`cora-output` is outside `.cora`, because everything under `.cora` is bookkeeping a
deployment may delete to start clean, and an itinerary you approved is not that. A
plugin writing there is handed the location rather than choosing one, and a name that
would resolve outside it — `..`, an absolute path, a symlink pointing away — is
refused after resolution rather than after a spell-check.

## Deleting

Nothing is deleted on your behalf, and each of the three rails deletes one thing at a
time, asking first.

- **A document** goes as its passages and its file, in that order, out of every upload
  the name covers. Passages leave both tables in one transaction. The order matters:
  a file left behind is unreachable and overwritten by the next upload of those bytes,
  while an index left behind hands out citations that open onto nothing.
- **A conversation** goes as its thread and then its turns. The thread first, so a
  failure halfway leaves a conversation still listed and still deletable rather than one
  reachable only by the model.
- **A fact** goes by its key. Forgetting everything reads to the end of the store first,
  which is what makes "everything" true.
- **A plugin** takes every field only it brought — those fields' documents, and every
  conversation pinned to them. What cora remembers about you stays, and so does anything
  an approved effect wrote, because those are yours rather than the field's.

## What this is not

There is no encryption, no user separation and no backup. The user column is there so a
second user costs a value rather than a schema change, but a deployment is one person's
machine, and `local` is the only user cora writes. A search needs the `sqlite-vec`
extension loadable — a CPython built with `SQLITE_OMIT_LOAD_EXTENSION` cannot open the
index at all, and says so as a retrieval failure.
