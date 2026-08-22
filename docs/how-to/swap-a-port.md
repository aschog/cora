# Swap the technology behind a port

Seven of the nine ports are arguments to `assemble`, so a different technology goes in a
slot without the engine changing.

1. **Write the class.** Match the port's methods and nothing else. A port is a
   `Protocol`, so there is no base class to inherit and no registration to do — the fit
   is structural, and `ty` checks it where the object is passed in:

   ```python
   class PgVectorRetriever:
       def add(self, chunks, vectors, file_hash): ...
       def query(self, query_vector, k): ...
       def sources(self): ...
       def contains(self, file_hash): ...
   ```

   Raise the port's own error on failure — `RetrievalError` here — so the engine keeps
   reporting one kind of failure per port. [The ports reference](../reference/ports.md)
   has each surface.

2. **Pass it in.** `assemble` is the seam. Call it from your own entry point instead of
   `build`, which is the shipped composition root and the only place that names cora's
   own adapters:

   ```python
   from cora.app.assembly import assemble

   app = assemble(
       chat_model=OpenRouterChatModel(...),
       embedder=SentenceTransformerEmbedder(),
       retriever=PgVectorRetriever(...),
       documents=SqliteDocuments.at(".cora/documents.sqlite"),
       plugins=load_plugins(("cora.plugins.fitness",)),
   )
   ```

   Nothing else moves: the engine, the plugins and the frontends see the same `App`.

3. **Keep it out of the engine.** The new class belongs in `cora.adapters` or in your
   own package. `tests/guards/test_architecture.py` walks every shipped file and fails
   the build if `cora.engine` imports a technology.

The two that are not arguments arrive another way: the loader registry is fixed inside
`assemble` (see [add a file format](add-a-file-format.md)), and a plugin comes in the
plugin set, which *is* an argument (see [write a plugin](write-a-plugin.md)).
