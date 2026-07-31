# Big picture

Read this page first. It shows the core of cora, its four ports, and the technology behind
each port. The design is called *hexagonal* (also known as *ports and adapters*).
The tests show how the code really works. The plans in `docs/plans/` show how
the code was built, not how it works today.

## The map

```mermaid
%%{init: {"flowchart": {"nodeSpacing": 45, "rankSpacing": 55, "curve": "basis"}}}%%
flowchart TB
  subgraph shell["cora.app"]
    ui["UI<br/><i>Streamlit widgets</i>"]
    root["Composition root<br/><i>loads plugin, binds ports, picks strategy</i>"]
  end

  subgraph core["cora.core"]
    engine["ChatEngine"]
    val["ValidationPipeline"]
    retr["Retrieval strategy<br/><i>plain · RAG-Fusion · hybrid</i>"]
    kb["KnowledgeBase"]
    rt["ToolRuntime"]
  end

  subgraph seam["cora.core.ports"]
    cm{{"ChatModel"}}
    emb{{"Embedder"}}
    ret{{"Retriever"}}
    plug{{"Plugin"}}
  end

  subgraph infra["cora.adapters · cora.plugins"]
    orc["OpenRouterChatModel<br/><i>LangChain</i>"]
    ste["SentenceTransformerEmbedder<br/><i>all-MiniLM-L6-v2</i>"]
    chroma["ChromaRetriever<br/><i>Chroma</i>"]
    bm25["Bm25KeywordIndex<br/><i>rank_bm25</i>"]
    fit["fitness plugin"]
  end

  ui -->|"answer()"| engine
  ui -->|"add_file()"| kb
  root ==> engine
  root ==> kb
  root ==> plug
  engine --> cm
  engine --> retr
  engine --> val
  engine --> rt
  retr --> kb
  kb --> emb
  kb --> ret
  retr -.->|"hybrid"| bm25
  cm -.-> orc
  emb -.-> ste
  ret -.-> chroma
  plug -.-> fit

  classDef port fill:#8c4b00,stroke:#d98a1f,color:#fff;
  classDef logic fill:#134e6f,stroke:#1f78b4,color:#fff;
  class cm,emb,ret,plug port;
  class engine,val,retr,kb,rt logic;
```

Read the map from top to bottom. The shell (top) calls the core (middle). The core has four
ports. When the app starts, each port is connected to one adapter (bottom). The core does not
know which adapter it uses.

| Mark | Means |
|---|---|
| blue box | A part of the core. It is plain Python, so a test can build it with fakes. |
| amber hexagon | A port — a slot in the core for one kind of technology. The four ports are the only way in and out of the core. |
| thin arrow | A call made while answering a request. |
| thick arrow | Built by the composition root when the app starts. |
| dotted arrow | The adapter behind a port. Change this one line to use a different technology. |

**Ingestion** and the **plugin registry** are real parts of the code. To keep the map simple,
they are shown inside KnowledgeBase and the composition root.

The **retrieval strategy** is the part that changes with the setting `CORA_RETRIEVAL`. There
are three options:

- `plain` — just use KnowledgeBase.
- `advanced` — use RAG-Fusion. A `QueryPlanner` writes the question in a few different ways, and RRF joins the results. (RRF, Reciprocal Rank Fusion, is a simple way to merge ranked lists.)
- `hybrid` — run two searches over the same files, one by meaning (dense) and one by keywords (BM25), and join them with the same RRF. This needs no planner and no extra model call.

A **port** is a fixed slot in the core for one kind of technology. The core has exactly four
slots: one for chat, one for embedding, one for retrieval, and one for the plugin. You can put a
different technology in a slot without changing the core.

BM25 has no slot like this. Only the `hybrid` search uses it, wired straight into that search.
So BM25 is a technology with no port. It is kept with the other adapters, and the core still has
just four ports.

## Two calls in

The shell uses the core through two main methods: `answer()` and `add_file()` (plus
`list_sources()` to show the file list in the sidebar).

**`engine.answer(question, history=()) -> ChatResult`** — `core/services/chat_engine.py`

1. **Validate** — check the question against the core rules (not empty, at most 4000 characters, no prompt-injection), then the plugin's rules. If a rule says no, raise `InputRejectedError`. The model never sees the question.
2. **Retrieve** — find the best `k` text chunks (small pieces of your documents; `CORA_TOP_K`, default 5) using the retrieval strategy above.
3. **Prompt** — build the message for the model in this order: the plugin's system prompt, the chunks numbered `[1]`…`[n]` with the rule to cite them, the last `CORA_HISTORY_TURNS` turns of chat (default 20; `0` means no memory), and last the question. Steps 1 and 2 use the question only, never the chat history.
4. **Tool loop** — let the model call tools, at most `CORA_MAX_TOOL_ROUNDS` times (default 8). If it never finishes, raise `ToolLoopLimitError`.
5. **Return** — the answer, the sources it really used (only the `[n]` numbers that appear in the reply, with duplicates removed), and every tool result.

**`kb.add_file(data, filename) -> int`** — `core/services/knowledge_base.py`

1. **Dedupe** — make a SHA-256 hash of the file. If the store already has this hash, stop and return `0`.
2. **Ingest** — the file must be `.txt`, `.md`, or `.pdf`, at most 10 MB, and not empty after cleaning. Each problem raises its own `IngestionError`.
3. **Chunk** — cut the text into pieces of 1000 characters that overlap by 150. Cut at the largest natural break that fits: paragraph, then line, then space, then single character.
4. **Embed and store** — turn each chunk into a vector (a list of numbers) and save it with its origin (source, index, offset, file hash). Return the number of chunks.

## The components

Nine parts, each with one job. Seven are on the map; two are marked *folded* because the map
shows them inside another part.

| Component | Job | Where |
|---|---|---|
| **ChatEngine** | The one main use case. It runs the steps in order: validate, retrieve, prompt, tool loop. It gets its helpers as inputs. | `core/services/chat_engine.py` |
| **KnowledgeBase** | A simple front for ingest, embed, and store. It also does search, lists sources, and skips files already uploaded. | `core/services/knowledge_base.py` |
| **Ingestion** *(folded)* | Turns bytes into clean text, then into overlapping chunks with their origin. Rejects the wrong type, too large, or empty. | `core/services/ingestion.py`, `loaders`, `cleaning`, `chunker` |
| **Retrieval strategy** | How the engine gets its chunks: `plain` (KnowledgeBase), `advanced`, or `hybrid`. Both wrappers merge results with RRF. | `fusion_context_source.py`, `hybrid_context_source.py`, `query_planner.py`, `rank_fusion.py` |
| **ValidationPipeline** | A list of rules run in order: core rules first, then the plugin's. To add a check, add a rule; you do not change the code. | `core/services/validation.py` |
| **ToolRuntime** | Finds the tool, checks the arguments against its JSON Schema, runs it, and turns every result (even a crash) into a `ToolResult`. | `core/services/tool_runtime.py` |
| **Plugin registry** *(folded)* | Loads a plugin by its module path and checks it before the app starts: the prompt exists, tool names are unique, schemas are valid. | `core/services/plugin_registry.py` |
| **Composition root** | The only place that names a real adapter. It reads the settings, loads the plugin, picks the strategy, and returns an `App`. | `app/config.py`, `app/assembly.py`, `app/retrieval.py` |
| **UI shell** | Only widgets: the uploader, the chat, the sources and tool-result boxes, and error text shown exactly as the error gives it. | `app/ui/` |

## The ports

The four ports are the only outward surface of the core. Three of them are **Protocols** (the
technology). The fourth, **Plugin**, is a frozen **dataclass** (the domain — the topic the app
is about). So an adapter and a plugin work the same way: each one is chosen in one place.

| Port | Surface | Bound at startup to |
|---|---|---|
| **ChatModel** | `complete(messages, tools) -> ModelReply` | `OpenRouterChatModel` — the only file that uses LangChain. It talks to OpenRouter, an OpenAI-style endpoint set by `CORA_MODEL`. |
| **Embedder** | `embed(texts) -> list[list[float]]` | `SentenceTransformerEmbedder` — the all-MiniLM-L6-v2 model. It runs on your machine and loads only when first used. |
| **Retriever** | `add(chunks, vectors, file_hash)`, `query(query_vector, k, metadata_filter=None)`, `sources()`, `contains(file_hash)` | `ChromaRetriever` — a saved, built-in database that uses cosine distance. The optional filter limits a search to matching metadata (self-query). |
| **Plugin** | data only: `system_prompt`, `tools`, `validation_rules`, `seed_docs` | `cora.plugins.fitness` — change it with `CORA_PLUGIN`. It is a frozen dataclass, not a class you subclass. |

Set `CORA_DEBUG=1` to wrap the three technology ports in a logger (`cora.adapters.port_logging`).
It prints one short line each time data crosses a port. The core, the plugins, and the UI do
not notice any change.

## Backed by tests

- **The core cannot use a framework.** A test reads every `cora.core` file. If one imports LangChain, Chroma, sentence-transformers, Streamlit, or any outer layer, the test fails. A fake bad import is added on purpose to prove the test catches it.
- **Streamlit is used in one folder only.** No file outside `cora/app/ui` may import it. This is why you can really replace the user interface.
- **The engine does not depend on any real helper.** It defines its own small Protocols (`ContextSource`, `InputValidator`, `ToolExecutor`). Every helper is passed in when the engine is built.
- **A new topic needs no change to the core.** A plugin is a frozen dataclass. Point `CORA_PLUGIN` at another plugin and the topic changes. The word *fitness* never appears in the core.
- **A broken tool cannot break the chat, and users never see a stack trace.** ToolRuntime turns every tool failure into a `ToolResult` with an error message. Every `CoreError` has a message written for a person, and a tool loop that runs too long returns a friendly apology.
