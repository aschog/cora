# Story 1: The agent plans its own steps

**As a** user · **I want** to ask in my own words · **So that** I get an answer that took
whatever steps were needed

> **Given** an indexed document and a question needing both a lookup and a calculation
> **When** I ask it
> **Then** the answer uses both — and a question needing neither is answered without
> retrieving or calling a tool

Satisfies the hard bonus *Agentic RAG*: retrieval becomes a decision, not a fixed step.

## Test list

**Tiers:** unit unless marked — **(int)** integration, **(e2e)** browser, **(llm)** live
model.

#### The architectural claim

- [ ] a planted `import langgraph` inside `cora.core` is caught by the purity scan
      (`langgraph` joins `FORBIDDEN_FRAMEWORKS`)
- [ ] every core step object is callable with exactly one positional argument (guards
      LangGraph's silent `Runtime`/`RunnableConfig` injection)

#### Citations (`citations.py`)

- [ ] `build_context_block` continues numbering after already-registered sources — a
      second retrieval starts at `[3]` — and returns only the newly registered ones
- [ ] a source already registered keeps its number when retrieved again
- [ ] `cited_sources(text, sources)` returns only cited sources, ascending

#### Infrastructure failures stay visible

- [ ] `ToolRuntime` lets an `AdapterError` from a tool propagate instead of returning a
      `ToolResult`; a plain `Exception` still becomes one

#### The retrieval tool

- [ ] the tool searches the injected context source with the model's `query` at the
      configured `k` and returns its hits
- [ ] dispatched through `ToolRuntime`, a call with no `query` comes back as an
      `invalid arguments` tool error

#### `ToolStep`

- [ ] a plain tool call executes; the partial dict carries a `tool` message and the
      `ToolResult`
- [ ] a hit-list payload is rendered into a numbered context block, and the stored
      `ToolResult` renders that same text
- [ ] the block's new sources land in the partial dict; a second retrieval in the same run
      continues the numbering
- [ ] a search that finds nothing feeds back "no matching documents" and registers no
      source
- [ ] several tool calls in one round all run, in order *(migrated)*
- [ ] an unknown tool and malformed arguments come back as tool messages, not exceptions
      *(migrated)*

#### `ModelStep`

- [ ] the step completes with the state's messages and the bound tools, appending the reply
- [ ] a final reply sets `answer`; a tool-calling reply does not
- [ ] each visit adds one to `rounds`

#### `PrepareStep`

- [ ] an invalid question raises `InputRejectedError` and produces no messages
- [ ] messages come out as system, then recent history, then the question *(migrated)*
- [ ] history longer than `max_history_turns` drops the oldest; `0` sends none *(migrated)*
- [ ] the system message carries the plugin prompt plus the instruction to call
      `search_documents` and cite `[n]` — and no context block

#### Router

- [ ] a final reply routes to `done`; a tool-calling reply under budget routes to `tools`
- [ ] a tool-calling reply at `max_tool_rounds` raises `ToolLoopLimitError` with its
      friendly message

#### `Agent` facade

- [ ] `answer` seeds the initial state from question + history and returns the run's
      `answer`
- [ ] `ChatResult.sources` are only the cited ones, resolved against the registered sources
- [ ] `ChatResult.tool_results` carry the run's results in order

#### `LangGraphRunner`

- [ ] over trivial fake steps, `run` walks prepare → model → tools → model and returns a
      state whose reducers accumulated every partial dict
- [ ] a runaway graph under a tiny recursion limit surfaces as `ToolLoopLimitError`, never
      `GraphRecursionError`
- [ ] with an endlessly tool-calling model the core counter fires first — exactly
      `max_tool_rounds` model calls before the friendly error
- [ ] an `InputRejectedError` from `PrepareStep` leaves `invoke` unwrapped, so the UI's
      `except CoreError` still catches it

#### ⇄ Switchover (one commit: `assemble` stops building `ChatEngine`)

- [ ] `assemble` returns an app whose `agent` answers a scripted question end-to-end
      through the graph
- [ ] the model is offered `search_documents` alongside the plugin's tools, and the runtime
      dispatches it
- [ ] `App` exposes the configured `context_source` — plain → the knowledge base, advanced
      → `FusionContextSource`, hybrid → `HybridContextSource` (re-points the mode-wiring
      assertions, including `tests/test_hybrid_retrieval.py`)
- [ ] `CORA_DEBUG=1` still wraps the three technology ports — re-pointed off
      `app.engine.chat_model`
- [ ] a debug turn logs the retrieval and embedding ports **when the model calls the
      search tool** (the old assertion, re-pointed at the decision)
- [ ] history turns reach the model behaviourally (replaces `app.engine.max_history_turns`)
- [ ] a plugin tool named `search_documents` is rejected at assembly rather than silently
      shadowed
- [ ] **(e2e)** the browser answer still lists its cited source, with the stub scripting a
      `search_documents` call before its answer — run `-m e2e` by hand on this commit

#### Close

- [ ] **(llm)** a real model retrieves for a document question and answers a greeting
      without a tool call — the honest proof that the *decision* is the model's
