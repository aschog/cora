## Why

A document uploaded by mistake cannot be got rid of, so it is searched and cited for
good.

## What Changes

- A document in the documents rail can be deleted, from the control at the end of its row
- Deleting takes both halves of it: its passages out of the index, and its file off disk
- The rail lists a name, so deleting one deletes every upload of that name in that field
- The index goes first, so a delete that fails halfway leaves a file nothing can reach
- A field owns its documents, so the same file in another field is left where it is
- Deleting asks first, in the question the other two rails already raise
- A citation into a document that is no longer there says so in one sentence
- Modified capability `documents`, which says today what a field's documents are

## Impact

- `src/cora/ports/documents.py`, `src/cora/ports/retrieval.py` — a verb each, and the name-to-uploads read
- `src/cora/adapters/file_documents.py` — the file of one upload is deleted
- `src/cora/adapters/chroma_retriever.py` — one upload's passages leave the collection
- `src/cora/engine/knowledge_base.py` — the one call over both stores
- `frontends/react/src/cora/frontends/react/api.py` — `DELETE /api/documents/{scope}/{name}`, and what an unopenable passage says
- `frontends/react/ui/src/` — the row's control and the question, both of them already written
- `README.md` — that a document goes from both stores, and that a name means every upload of it
- Left alone: what ingestion does, and the order it does it in
- Left alone: the recorded turns that cited the document, which keep their citations
- Left alone: deleting one upload of a name, which the rail cannot show apart
