## Why

A plugin can search its field but not read it, so no tool of its own can list a log.

## What Changes

- The host hands a plugin every document its field holds, each as its name and its text
- They come in upload order, and two uploads of one name are two documents
- A document whose file is gone is left out, as a search leaves its passages out
- What a plugin read this way is labelled untrusted, as a searched passage is
- Capability `plugins` — a plugin is handed the field it runs in, beside search

## Impact

- `src/cora/ports/context_source.py` — one more question a plugin may ask of its documents
- `src/cora/engine/knowledge_base.py`, `src/cora/engine/host.py` — answer it, and label the answer
- `tests/helpers/fakes.py` — the fake index answers it too
- `docs/how-to/write-a-plugin.md` — one more line under what the host hands you
- Left alone: the retriever, the document store, the rail's listing, and every plugin shipped
