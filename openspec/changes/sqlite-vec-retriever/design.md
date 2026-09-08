## Context

- The `Retrieval` port hides the store behind six methods, and only one of them
  needs a vector.
- The index keeps spans and embeddings and no text, so nothing readable is at stake.
- Everything else cora keeps is a file it names, while Chroma keeps a directory of
  its own.
- Checked before choosing: `sqlite-vec` 0.1.9 loads on this project's Python, and
  SQLite 3.53.4 allows extensions.

## Goals / Non-Goals

**Goals:**

- The index is one SQLite file cora opens itself.
- A field's passages stay physically apart, as they are today.
- The port, the engine and the documents on disk go untouched.

**Non-Goals:**

- Merging the index with conversations, memory or checkpoints — the next change.
- Carrying a user through the port; the column exists, the plumbing does not.
- Tuning approximate search, which exact search at this scale does not need.

## Decisions

- Two tables rather than one: `passages` holds the spans and names, a `vec0` virtual
  table holds the vectors.
- Four of the six port methods never touch a vector, so they stay plain SQL over
  `passages`, joined by rowid.
- Rejected `vec0` auxiliary columns for the metadata, which would put every listing
  query behind the vector table.
- `scope` is `vec0`'s partition key, so a field's vectors sit apart rather than being
  filtered out of a shared set.
- Rejected a `where` clause on one table, because the adapter promises separation and
  not omission.
- The vector column declares `distance_metric=cosine`, which keeps distances in nought
  to one and the score conversion as it is.
- The `vec0` table is created on first write, taking its dimension from the vector
  handed in.
- Rejected a dimension constant, because the embedder is a port and its width is not
  cora's to name.
- A search before any write finds no table and answers empty, as an empty field does
  today.
- `passages` carries a `user` column set to `local`, because adding it later is an
  alter and a backfill.
- The extension loads on the adapter's own connection at construction, so a Python
  without extension support fails by name at startup.

## Risks / Trade-offs

- A build with extension loading disabled cannot run cora → the failure is at
  construction, named, rather than mid-search.
- `vec0` scans a partition exactly instead of indexing it → correct at this scale, and
  the ceiling gets a comment.
- Dropping `chromadb` changes what the environment resolves → two architecture guards
  name it in prose and need rewording, and `numpy` still arrives with
  sentence-transformers.
- A lazily created table hides a schema error until the first upload → the adapter's
  tests write before they read.

## Migration Plan

- No conversion is written: `.cora/` is cleared by hand, and the documents are uploaded
  again.
- Rollback is the previous commit, since the old store is gone either way.

## Touched

- Ports: none — `Retrieval` is unchanged.
- Guards: `test_reference_pages` names the module by path, `test_architecture` and
  `test_installs` name chromadb in prose.
- Diagrams: `component-map`, `upload-map` and `search-map` are redrawn.
