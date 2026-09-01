## Why

Cleaned text sits in a SQLite store nobody can read, and every field shares one pile of it.

## What Changes

- Cleaned text becomes one Markdown file per source, under a directory named for its scope
- The `Documents` port keeps and reads within a scope, and a file adapter fills it
- The index keeps embeddings and offsets only, and a hit's text is read back from its file
- A passage, a citation and a turn each carry the field they belong to
- A search sees the turn's scope alone, so no other field's passage is retrieved or cited
- An upload names the field it lands in, and one naming none lands in the default scope
- The rail offers the field to upload into, and lists the active field's documents
- `README.md` states the layout in a paragraph
- **BREAKING** `.cora/documents.sqlite` and the one collection go, and nothing is carried over
- New capability `documents`

## Impact

- `src/cora/ports/documents.py` — keeping, reading and listing all take the scope
- `src/cora/adapters/file_documents.py` — new: one Markdown file per source, per scope
- `src/cora/adapters/sqlite_documents.py` — deleted, with the tests that held it
- `src/cora/adapters/chroma_retriever.py` — scoped, storing spans rather than the text again
- `src/cora/ports/retrieval.py`, `src/cora/ports/context_source.py` — a search is asked within a scope
- `src/cora/engine/knowledge_base.py` — ingests into a scope, and reads a hit's text from its file
- `src/cora/engine/retrieval_tool.py`, `src/cora/engine/tool_runtime.py` — the turn's scope reaches the call
- `src/cora/app/config.py`, `src/cora/app/assembly.py` — one documents root replaces two store paths
- `frontends/react/` — the upload's field, the scoped listing, and the rail's picker
- `tests/guards/` — the component map redrawn from the assembly
- `README.md`, `docs/tutorial/first-session.md` — the layout, and the field an upload names
- Left alone: memory, threads, checkpoints, the brief, routing and the pin
