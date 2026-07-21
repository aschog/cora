# Feature Plan: Knowledge Base

Roadmap item 3 (`docs/plans/webapp-overview.md` §10). Branch: `feature/knowledge-base`.

## Requirements

From the architecture plan (§3 ports, §4 Knowledge Base, §6 flows, §8 tiers):

- Introduce the **embedder** and **retriever** ports (narrow, core-owned). The chat-model port is deferred to item 6, where its first consumer appears.
- Provide **in-memory fakes** for both so all core logic runs in the unit tier — no network, no model downloads, no vector store. The fakes double as proof the ports suffice.
- Provide the two real **adapters**, one volatile dependency each: **Chroma** (embedded + persistent) retriever and lazy-loaded **sentence-transformers** embedder. Exercised only in the integration tier.
- Provide the **Knowledge Base facade**: `add_file` (ingest via `docchat.ingestion.ingest` → embed → store with provenance), `list_sources`, `search`.
- **Dedupe re-uploads** by content hash: re-adding a file is idempotent and short-circuits before the embed step.
- Adapter failures surface as typed `DocChatError`s with user messages; no `chromadb`/`sentence-transformers` exception escapes its adapter.

**Acceptance:** facade ingests a doc, lists it, and returns relevant chunks with provenance — in the unit tier against fakes and end-to-end with real adapters in the integration tier; re-uploads change nothing; all gates green.

## Design (architecture level)

The facade *delegates* to two ports; each is a narrow interface with a unit-tier fake and an integration-tier real adapter. The core imports no vendor library.

```mermaid
classDiagram
  class KnowledgeBase {
    +add_file()
    +search()
    +list_sources()
  }
  namespace Embedding {
    class Embedder {
      <<interface>>
      +embed()
    }
  }
  namespace Retrieval {
    class Retriever {
      <<interface>>
      +add()
      +query()
    }
  }
  KnowledgeBase --> Embedder : delegates
  KnowledgeBase --> Retriever : delegates
```

`Embedder` and `Retriever` are the two ports the facade requires. Each is provided by a unit-tier **fake** and an integration-tier **real adapter** (Chroma, sentence-transformers) implementing the identical interface, so the facade runs against either without change — the hexagonal seam that keeps the core vendor-free and unit-testable.

The two use-case flows the facade drives:

```mermaid
sequenceDiagram
    actor UI
    UI->>KnowledgeBase: add_file(data, filename)
    KnowledgeBase->>KnowledgeBase: sha256(data)
    alt already ingested
        KnowledgeBase-->>UI: no-op (dedupe)
    else new file
        KnowledgeBase->>Ingestion: ingest()
        KnowledgeBase->>Embedder: embed(chunk texts)
        KnowledgeBase->>Retriever: add(vectors + provenance)
        KnowledgeBase-->>UI: chunks added
    end
```

```mermaid
sequenceDiagram
    actor UI
    UI->>KnowledgeBase: search(query, k)
    KnowledgeBase->>Embedder: embed(query)
    KnowledgeBase->>Retriever: query(vector, k)
    Retriever-->>KnowledgeBase: hits
    KnowledgeBase-->>UI: chunks + provenance + score
```

- **Two ports (Ports & Adapters / Strategy).** Embedder: text → vectors. Retriever: a pure vector index (store records, query by vector for top-k). Each is independently fakeable and confines one dependency.
- **Embedding lives in the facade, above the retriever port.** The facade owns both embed calls (documents on ingest, query on search), so the same embedder embeds both sides. The retriever stays a thin vector store mapping directly onto Chroma's precomputed-`embeddings=` path; Chroma's own model is never invoked.
- **The port speaks relevance scores, not raw distances** (higher = more relevant). The fake computes cosine similarity; the Chroma adapter translates its distance metric to the same convention. Cosine space + unit-normalized vectors, chosen deliberately.
- **Retrieved chunk = value object:** text + provenance (source, index, offset) + score; immutable, equality by content — the input to citation rendering. Extends the `Chunk` value-object pattern.
- **Facade (Facade pattern)** holds no technology — depends only on the two ports, so tests wire fakes and the composition root (item 6) wires adapters.
- **Dedupe (stdlib `hashlib`).** Hash the file bytes; derive deterministic per-chunk ids from hash + index; skip before embedding if the hash is already stored. First-write-wins (`add`). Hash stored as a string metadata field (Chroma metadata is `str|int|float|bool`).
- **Confinement.** `chromadb` in one module, `sentence-transformers` in one; the embedder lazy-loads its model on first use (import stays cheap, model out of the unit tier). Each adapter catches its library's exceptions and re-raises typed errors.
- **Tiers.** This branch introduces the integration tier and the first `conftest.py` (per-test temp dir + unique collection name so Chroma state never leaks).

## TDD checklist

Each item is one red → green → refactor cycle; commit each green step. Ordered bottom-up. **(integration)** items carry `@pytest.mark.integration`.

**Retrieved-chunk value object**
- [ ] a retrieved chunk is immutable: text + provenance + score, equal by content, mutation fails

**Fake embedder**
- [ ] maps texts to deterministic fixed-dim vectors: identical text → identical vector, different texts differ, a batch embeds element-wise

**Fake retriever**
- [ ] querying an empty retriever yields no hits, no error
- [ ] returns stored records ordered most-relevant-first by cosine similarity, capped at k, each hit carrying provenance + score
- [ ] k larger than the store returns every record; the closest vector ranks first

**Facade (against both fakes)**
- [ ] `add_file` ingests, embeds every chunk once, stores one record per chunk with provenance; reports chunks added
- [ ] `search` returns the top-k relevant chunks, ordered, with provenance + score (a query equal to a chunk's text retrieves that chunk first — proves query and docs share one embedder)
- [ ] `search` on an empty KB returns no hits, no error
- [ ] `list_sources` returns each source once across multiple files
- [ ] re-adding identical bytes is a no-op: no duplicate chunks, source listed once, embedder not called again
- [ ] a rejected ingestion (unsupported/empty/oversized) propagates its typed error unchanged

**Errors**
- [ ] the adapter error categories (embedding failed, retrieval failed) are `DocChatError` subtypes with user messages

**Chroma adapter** (`uv add 'chromadb>=1.5,<2'` at the first red step)
- [ ] **(integration)** round-trips with our own precomputed embeddings (no Chroma embedding function): query returns records ordered by relevance with provenance + scores
- [ ] **(integration)** records persist across a fresh client on the same directory
- [ ] **(integration)** content-hash ids make re-adds idempotent (no duplication)
- [ ] **(integration)** a Chroma failure surfaces as the typed retrieval error

**sentence-transformers adapter** (`uv add 'sentence-transformers>=5.3,<6'` at the first red step)
- [ ] **(integration)** lazy-loaded: importing the module loads nothing; model built on first embed
- [ ] **(integration)** encodes texts to 384-dim unit vectors; identical text → identical vector

**End-to-end**
- [ ] **(integration)** facade with both real adapters ingests a doc and retrieves the relevant chunk, provenance intact

## Rejected alternatives

- **Embedding inside the retriever adapter** — couples both dependencies, forces the fake to embed, risks docs/queries using different models.
- **`upsert` over `add`** — content-hash ids make both idempotent; first-write-wins is simpler.
- **Chroma's own embedding function** — downloads a second model, splits the embedding source, breaks confinement.
- **Raw distances through the port** — metric-specific; a normalized score keeps core, fake, and UI on one convention.
- **Richer provenance / a distinct store-record type** — `source, index, offset` already suffice and map straight to metadata.
