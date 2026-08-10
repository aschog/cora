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
model. **(migrated)** marks a test that moves off `ChatEngine` rather than a new one.

#### The architectural claim

- [x] a `langgraph` import into a core module is detected as forbidden — mirrors the
      `rank_bm25` proof, and turns green when `langgraph` joins `FORBIDDEN_FRAMEWORKS`

#### Citations (`citations.py`, home of `Source`, `Context` and the citable hit list)

- [x] `cited_numbers` reads distinct numbers in order of first appearance, and none from
      uncited text *(migrated)*
- [x] it ignores brackets glued to a word or another bracket *(migrated)*
- [x] it reads every number in a consecutive run, multi-digit included *(migrated)*
- [x] against an empty registry, a batch numbers from `[1]`, one number per unique source,
      a repeated source keeping its number *(migrated)*
- [x] `build_context_block` continues numbering after already-registered sources — a
      second retrieval starts at `[3]`
- [x] it returns only the newly registered sources
- [x] a source already registered keeps its number when retrieved again
- [x] the block marks its document text as untrusted data, not instructions
- [ ] a hit list registered against the sources known so far renders as that block and
      names the sources it added
- [ ] a hit list with no hits renders as "no matching documents" and adds none
- [ ] `cited_sources(text, sources)` returns only cited sources, ascending
- [ ] a citation whose number has no registered source is ignored *(migrated)*

#### Infrastructure failures stay visible

- [ ] `ToolRuntime` lets an `AdapterError` from a tool propagate instead of returning a
      `ToolResult`
- [ ] a plain `Exception` from a tool still becomes a `ToolResult` error *(migrated)*

#### The retrieval tool (`retrieval_tool.py`; `ContextSource` moves to `context_source.py`)

- [ ] the tool searches the injected context source with the model's `query` at the
      configured `k` and returns its hits as a citable payload
- [ ] dispatched through `ToolRuntime`, a call with no `query` comes back as an
      `invalid arguments` tool error

#### `ToolStep`

- [ ] a plain tool call executes; the partial dict carries a `tool` message and the
      `ToolResult`
- [ ] a payload that registers no citations is fed back by `ToolResult.render()` unchanged
- [ ] a citable payload is registered against the run's known sources, and the stored
      `ToolResult` renders the block it produced
- [ ] the sources it added land in the partial dict
- [ ] a second citable payload in the same run continues the numbering
- [ ] a second *tool* returning a citable payload is registered the same way — the step
      names no tool
- [ ] several tool calls in one round all run, in order *(migrated)*
- [ ] an unknown tool comes back as a tool message, not an exception *(migrated)*
- [ ] malformed arguments come back as a tool message, not an exception *(migrated)*

#### `ModelStep`

- [ ] the step completes with the state's messages and the bound tools, appending the reply
- [ ] a tool-calling reply is appended with its `tool_calls` intact, ahead of the tool
      messages the round adds
- [ ] a final reply sets `answer`; a tool-calling reply does not
- [ ] each visit adds one to `rounds`
- [ ] an `LlmError` from the chat model propagates unchanged *(migrated)*

#### `PrepareStep`

- [ ] an invalid question raises `InputRejectedError` and produces no messages
- [ ] the validator sees the question alone, never the history *(migrated)*
- [ ] messages come out as system, then recent history, then the question *(migrated)*
- [ ] history longer than `max_history_turns` drops the oldest *(migrated)*
- [ ] history exactly at the cap is sent in full *(migrated)*
- [ ] an odd cap sends a leading assistant turn without its question *(migrated)*
- [ ] `0` sends no history at all *(migrated)*
- [ ] the system message carries the plugin prompt plus the instruction to call
      `search_documents` and cite `[n]`

#### Router

- [ ] a final reply routes to `done`
- [ ] a tool-calling reply under budget routes to `tools`
- [ ] a tool-calling reply at `max_tool_rounds` raises `ToolLoopLimitError` with its
      friendly message

#### `Agent` facade (`agent.py`, home of `ChatResult`)

- [ ] `answer` seeds the initial state from question + history and returns the run's
      `answer`
- [ ] `ChatResult.sources` are only the cited ones, resolved against the registered sources
- [ ] `ChatResult.tool_results` carry the run's results in order
- [ ] over a turn that retrieves, no document text reaches the system message — it exists
      only in `tool` messages

#### `LangGraphRunner` (`adapters/`, behind the new `GraphRunner` port in `core/ports/graph.py`)

- [ ] over trivial fake steps, `run` walks prepare → model → tools → model
- [ ] the returned state's reducers accumulated every partial dict
- [ ] a runaway graph under a tiny recursion limit surfaces as `ToolLoopLimitError`, never
      `GraphRecursionError`
- [ ] with an endlessly tool-calling model the core counter fires first — exactly
      `max_tool_rounds` model calls before the friendly error
- [ ] an `InputRejectedError` from `PrepareStep` leaves `invoke` unwrapped, so the UI's
      `except CoreError` still catches it
- [ ] an `AdapterError` raised inside a step leaves `invoke` unwrapped too

#### ⇄ Switchover (one commit: `assemble` stops building `ChatEngine`)

- [ ] `assemble` returns an app whose `agent` answers a scripted question end-to-end
      through the graph
- [ ] the model is offered `search_documents` alongside the plugin's tools, and the runtime
      dispatches it
- [ ] `assemble(top_k=…)` reaches the search tool *(migrated)*
- [ ] `assemble(max_tool_rounds=…)` reaches the round budget *(migrated)*
- [ ] the plugin's system prompt reaches the model *(migrated)*
- [ ] history turns reach the model behaviourally (replaces `app.engine.max_history_turns`)
- [ ] the assembled agent rejects an injection attempt before the model is called
      *(migrated)*
- [ ] it chains core and plugin validation rules, in that order *(migrated)*
- [ ] `App` exposes the configured `context_source` — plain → the knowledge base *(migrated)*
- [ ] advanced → `FusionContextSource`, built with the configured query count *(migrated)*
- [ ] hybrid → `HybridContextSource` (re-points `tests/test_hybrid_retrieval.py` too)
      *(migrated)*
- [ ] `CORA_DEBUG=1` still wraps the three technology ports — re-pointed off
      `app.engine.chat_model`
- [ ] a debug turn logs the retrieval and embedding ports **when the model calls the
      search tool** (the old assertion, re-pointed at the decision)
- [ ] a chat turn stays silent without debug *(migrated)*
- [ ] a plugin tool named `search_documents` is rejected at assembly rather than silently
      shadowed
- [ ] **(int)** the UI answers through `app.agent` and its Sources panel lists the cited
      source, with the model scripting a `search_documents` call *(migrated)*
- [ ] **(e2e)** the browser answer still lists its cited source, with the stub scripting a
      `search_documents` call before its answer — run `-m e2e` by hand on this commit

#### Close

- [ ] **(llm)** a real model retrieves for a document question and answers a greeting
      without a tool call — the honest proof that the *decision* is the model's
