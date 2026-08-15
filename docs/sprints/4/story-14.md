# Story 14: One way to search

**As a** user asking about my documents · **I want** one search path, the one the trace
shows · **So that** what cora did to answer me is what I can read back, and nothing
rewrites my question where I cannot see it

> **Given** cora running with nothing configured about retrieval
> **When** I ask a question about an uploaded document
> **Then** I get an answer citing that document, and every model call the run made is a
> step in the trace

`advanced` mode was sprint 3's answer to "advanced RAG with query translation": a
`QueryPlanner` rewrites the question into four phrasings, `FusionContextSource` runs each
one and RRF merges the rankings — all behind `search_documents`, before the knowledge
base is reached. The agent now does that job in the open. It re-searches when the
passages are thin, story 8's gate makes it take a second look, and each call is a trace
step. What is left of the planner is a second model call per search that nothing can see,
and `plain` has been the default the whole time.

## What goes

| | |
|---|---|
| `engine/query_planner.py` · `engine/fusion_context_source.py` · `engine/rank_fusion.py` · `domain/query_plan.py` | the mode itself |
| `app/retrieval.py` | a builder registry with one entry left is a switch with ceremony |
| `CORA_RETRIEVAL` · `CORA_FUSION_QUERIES` | nothing left to choose |
| `domain/metadata_filter.py`, and the `metadata_filter` argument through `ports/retrieval.py`, `engine/knowledge_base.py`, `adapters/chroma_retriever.py`, `engine/port_logging.py` | the planner was its only caller |

`KnowledgeBase` becomes the `ContextSource` the search tool holds, with no mode to pick,
and `assembly` stops needing a `ChatModel` to build retrieval at all — the planner was
the only reason searching knew about the model. `list_sources` stays: the sidebar lists
what you uploaded.

## Test list

**Tiers:** unit unless marked — **(int)** integration.

#### First, the outer test

This story subtracts, so its outer test is green before the first deletion and has to
stay green through every one — a characterization test, not an `xfail`. It is the bar:
red at any point means the subtraction took something with it.

- [ ] **(int)** a question against a real index is answered from the uploaded document
      and cites it, with nothing configured about retrieval

#### Searching is the knowledge base, with nothing in front of it

- [ ] the app's search tool returns the knowledge base's own hits — a run that answers
      one question makes exactly one model call, so no rewriter sits between the tool
      and the index
- [ ] the app assembles with no retrieval mode and no chat model reaching retrieval

#### Config forgets the knobs

- [ ] `CORA_RETRIEVAL` in the environment is not read, and no longer refuses a value it
      does not know — there is no mode to name
- [ ] `CORA_FUSION_QUERIES` in the environment is not read

#### A query is a query

- [ ] `ChromaRetriever.query` asks for top-k with no `where` clause and returns what it
      found **(int)**
- [ ] the retriever's log line names the query and the number of hits, with no filter
      to describe

#### The docs still describe the tree

- [ ] every location the docs claim exists — `big-picture.md`, `happy-path.md` and
      `README.md` stop naming the planner, the fusion source and the two env vars

## Out of scope

- **A `source` parameter on `search_documents`.** Scoping a search to one document is
  the one thing the planner could do that the agent cannot. Nothing asks for it today,
  so it does not get built today; when something does, it arrives as a tool parameter
  the agent chooses and the trace shows, and this story is what makes that version
  small.
- **A deprecation path for the two env vars.** They stop being read. A stale `.env` is
  ignored, not refused.
- **Hybrid search.** Left in story 13, not coming back.
- **The retrieval seam.** `ContextSource` stays a port with one implementation: it is
  what the search tool holds, and what tests fake.
