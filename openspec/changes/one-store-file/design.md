## Context

- See proposal.md — Why. The index became a SQLite file in `sqlite-vec-retriever`, which
  this change builds on.
- Two of the four stores already share `conversations.sqlite`: the recorded turns and
  LangGraph's checkpoints.
- Each store owns its own tables and opens its own connection, so sharing a file is
  already the house pattern.
- `SqliteStore` and `SqliteSaver` create what they need through `setup()`, and neither
  minds a file another table lives in.

## Goals / Non-Goals

**Goals:**

- One database file, named by one setting.
- Every store keeps its own connection, its own tables and its own error type.
- A deployment that pointed the old variables somewhere is told, not silently ignored.

**Non-Goals:**

- Merging the tables themselves: a fact and a turn stay unrelated rows.
- One transaction across two stores, which nothing needs and no port offers.
- Moving the documents, which stay readable files under their own root.

## Decisions

- The setting keeps the name `CORA_DB_PATH`, because it already names the database and
  a third name would be a third thing to learn.
- The two retired variables are dropped rather than deprecated, since no deployment of
  cora is older than this sprint.
- WAL is left as SQLite's default under these connections, because four readers of one
  file is what it was built for.
- Rejected one shared connection: each adapter's lifetime and error translation are its
  own, and a shared handle makes closing one close them all.
- Rejected a migration: the stores were cleared for the retriever change, so there is
  nothing to carry.
- The privacy page's store guard reads the `DEFAULT_*_PATH` constants, so deleting two
  of them is what makes the page red until it is rewritten.

## Risks / Trade-offs

- Four connections on one file can contend under concurrent writes → WAL takes
  concurrent readers with one writer, which is what a single-user deployment does.
- One file cannot be thrown away in parts any more → losing the index alone stops being
  `rm -rf`, and re-uploading is the way back.
- A deployment still setting the retired variables gets the default instead → the
  breaking change is named in the commit and the pull request, since this repo keeps no
  release note.

## Migration Plan

- None: `.cora` is cleared, and the first run creates the file.
- Rollback is the previous commit, since the old three-file layout is gone either way.

## Touched

- Ports: none.
- Guards: `test_docs`'s store table, which derives its rows from the config constants.
- Diagrams: none — the component map names adapters and ports, not paths.
