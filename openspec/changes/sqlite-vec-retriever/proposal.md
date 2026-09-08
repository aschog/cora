## Why

Chroma keeps a directory of its own for spans and vectors cora could hold in its own
store.

## What Changes

- `SqliteVecRetriever` replaces `ChromaRetriever` behind the unchanged `Retrieval` port.
- The index becomes one SQLite file: a `passages` table beside a `vec0` virtual table.
- A field stays physically apart, as `vec0`'s partition key rather than a collection.
- `passages` carries a `user` column, `local` for now, so multi-user needs no backfill.
- **BREAKING** `CORA_DB_PATH` names a file, where it named a directory.
- **BREAKING** every store under `.cora/` is cleared; documents are uploaded again.
- `chromadb` leaves the dependencies and `sqlite-vec` arrives.

## Impact

- `src/cora/adapters/chroma_retriever.py` — deleted; `sqlite_vec_retriever.py` replaces it
- `src/cora/app/assembly.py`, `src/cora/app/config.py` — the index path is a file
- `tests/cora/adapters/test_chroma_retriever.py` — becomes the new adapter's tests
- `pyproject.toml`, `uv.lock` — `chromadb` out, `sqlite-vec` in
- `tests/guards/test_reference_pages.py` — the module it names by path
- `tests/guards/test_architecture.py`, `tests/guards/test_installs.py` — what they say
  chromadb drags in
- `docs/assets/component-map.svg`, `upload-map.svg`, `search-map.svg` — redrawn
- `README.md`, `docs/privacy-and-ethics.md`, `docs/big-picture.md` — where the index lives
- Leaves alone: the `Retrieval` port, the engine, the documents on disk, memory and
  conversations
