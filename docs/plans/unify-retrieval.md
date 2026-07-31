# One retrieval port, no duplication

The project's rule is *one abstraction per idea, extend by adding not editing*. Retrieval
breaks it: the single idea "search for ranked chunks" is declared under four names
(`ContextSource`, `SearchIndex`, `KeywordStore`'s search half, and — richer — `DocumentIndex`),
the retrieval *mode* is chosen by a hand-edited `if/elif` fanned across `assembly.py` and
`config.py`, and two small blocks are copy-pasted. Collapse the duplication; leave genuinely
distinct capabilities alone.

## Acceptance criteria

- `search(query, k) -> list[RetrievedChunk]` is declared **once** (`ContextSource`); every
  retrieval source (KnowledgeBase, Bm25KeywordIndex, Fusion, Hybrid) satisfies that one name.
- Adding a retrieval mode is **one registry entry**, not edits to `_context_source` +
  `RETRIEVAL_MODES` + validation.
- The `ToolResult`→string branch and the Chroma chunk-from-metadata block each live in one place.
- **Behaviour is unchanged** — plain/advanced/hybrid retrieval, tool output, and UI all identical.

## Design

- **One read port.** Keep `ContextSource` (`search(query, k)`) in `chat_engine.py`. Delete
  `SearchIndex` (a byte-identical alias); type `HybridContextSource.dense/keyword` as
  `ContextSource`. Bm25KeywordIndex already matches it — no adapter change.
- **Compose, don't re-declare.** `KeywordStore` (the injected sparse index, needs `add` +
  `search`) becomes `class KeywordStore(KeywordIndex, ContextSource, Protocol)` — inherits both
  methods, declares neither twice. `KeywordIndex` (write, `add`) stays: it's the ingestion
  fan-out, a distinct concern.
- **Keep the one richer port.** `DocumentIndex` (`search` + `metadata_filter` + `list_sources`)
  is what Fusion's self-query genuinely needs — not a duplicate, a bigger capability. Leave it
  (optional polish: rename → `SelfQueryIndex` to make the distinction obvious).
- **Mode registry.** Replace `_context_source`'s `if/elif` and the separate `RETRIEVAL_MODES`
  tuple with one dict keyed by mode → builder (mirrors the existing `LOADERS` registry).
  Allowed modes derive from its keys; the hybrid builder owns building the keyword index.
- **De-dupe.** Extract `render_tool_result(result) -> str` into core, called by
  `chat_engine._tool_message` and `ui/formatting.format_tool_result`. Extract
  `_to_chunk(document, metadata)` in `chroma_retriever`, used by `query` and `all_chunks`.

## TDD checklist

- [ ] `KeywordStore` recomposed from `KeywordIndex` + `ContextSource`; assembly + fakes green.
- [ ] `HybridContextSource` slots typed `ContextSource`; `SearchIndex` deleted; hybrid tests green.
- [ ] Mode registry replaces the `if/elif` + `RETRIEVAL_MODES`: unknown mode rejected, each mode
      builds its expected source type, and a newly registered mode works with no dispatch edit.
- [ ] `render_tool_result` extracted; `_tool_message` and `format_tool_result` both call it;
      tool-message and UI output unchanged.
- [ ] `_to_chunk` extracted in `chroma_retriever`; `query`/`all_chunks` unchanged (integration green).
- [ ] *(optional)* rename `DocumentIndex` → `SelfQueryIndex`; fusion tests green.

## Out of scope

- **Loaders** — `loaders.py` is *already* a data registry (the pattern adopted above); letting
  plugins contribute loaders is a new feature, not a duplication.
- **`ValidationRule` vs `InputValidator`** — genuinely different roles (one rule vs the pipeline).
- **Library-exception → `CoreError`** done three ways — an inconsistency, not duplication; own task.

## Fallout

- Tests: collapse `FakeDocumentIndex` / `_FakeKeywordStore` / `FakeContextSource` toward the one
  read port; the `ContextSource`/`InputValidator`/`ToolExecutor` claim in `big-picture.md` stays
  true (ContextSource does not move). Update the retrieval prose to "five names → one".
- Gates: pure refactor, so integration/e2e/llm need no behavioural change — only unit tests move.
