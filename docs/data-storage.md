# Where your data lives

Two shapes, both on your own machine: one SQLite file cora keeps for itself, and files
you can read beside it. Which paths, and what moves each, is the table in
[privacy](privacy-and-ethics.md#what-is-kept-and-where).

## One file, five writers

`.cora/cora.sqlite` holds five writers, in six tables. One file, so a deployment moves all of it by
naming one path and a backup is one file. Write-ahead logging and autocommit, because
four writers and every reader of the page share it. Nothing migrates: every table is
made by the first writer that needs it.

- **Passages** — one row per chunk: the field, the filename, the position, and the
  offset and length of the span. Not the text.
- **Vectors** — a `sqlite-vec` table keyed by the same row id, cosine, with the field as
  its partition key, so a field's vectors sit apart rather than behind a `where`. Its
  width is the first vector's, and the file keeps it.
- **Facts** — LangGraph's store under a namespace of cora's. A fact's key is a
  nanosecond ordinal, because the store's own timestamps tie at one second.
- **Turns** — one row per turn, in the order they were taken: the question, the answer,
  the citations, the fields, and the trace as JSON, each step tagged with its kind so a
  nested one reads back as what it was.
- **What a plugin keeps** — LangGraph's store again, under `kept` and then the plugin's
  own name, one row per name it wrote. Nothing reads it but the plugin that wrote it:
  it is not searched, not cited, not recalled and not in any brief.
- **Checkpoints** — LangGraph's saver: the brief, the transcript, the tool results, what
  a plugin kept, the pin, and any card the turn stopped on. Beside the turns, because a
  deployment deleting the file should lose both or neither.

## Documents are files you can open

`.cora/documents` is a directory per field, holding one Markdown file per upload — the
cleaned text and nothing else, because a citation's offsets are positions in it. The
name carries the head of the upload's hash, so one filename uploaded twice is two files
and the store is its own index. A field is a directory here, so its name is checked
before a byte is written.

## What an effect wrote is not cora's

`cora-output` sits outside `.cora`, because everything under `.cora` is bookkeeping a
deployment may delete and an itinerary you approved is not. A plugin is handed the
location rather than choosing one, and a name that would resolve outside it is refused
after resolution — so `..`, an absolute path and a symlink are all read as what they
would really reach.

## Deleting

- **A document** — its passages out of both tables in one transaction, then the file.
  The rail lists a name and the stores keep uploads, so deleting a name takes every
  upload of it in that field, and the same file in another field is left alone.
  That order: a file left behind is unreachable and overwritten by the next upload of
  those bytes, while an index left behind cites a file nobody can open.
- **A conversation** — the thread first, then its turns, so a failure halfway leaves it
  listed and deletable rather than reachable only by the model.
- **A fact** — by its key. Forgetting everything reads to the end of the store first.
- **A plugin** — every field only it brought. What that leaves is
  [what cora does](what-it-does.md#deleting-what-it-holds).

## What this is not

No encryption, no user separation, no backup. `local` is the only user cora writes — the
column exists so a second one costs a value rather than a migration. A search needs the
`sqlite-vec` extension loadable: a Python built without extension loading cannot open
the index at all, and says so as a retrieval failure.
