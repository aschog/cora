# Story 15: The turn is one path

**As a** developer of cora · **I want** a turn to run model → tools → done and nothing
else · **So that** the graph is one path I can hold in my head

> **Given** a plugin that names a domain and a document indexed under it
> **When** the model answers without calling the search tool
> **Then** the answer stands as given — no second search, no send-back, and no
> reconsideration in the trace

Reverses story 8, and story 12 with it — the two silences are `GroundStep`'s. What
survives is the empty store the *search tool* meets (`EMPTY_STORE`, `AGENT_RULES`), so
cora still asks for documents on a turn where the model searches, and says nothing on a
turn where it doesn't. The backlog's *No grounding or scope decision*
(`sprint-4-feedback.md:38`) is knowingly reopened: the instruction to search and cite
stays in `AGENT_RULES` and in the fitness plugin's prompt, enforcement goes.

## Test list

**Tiers:** unit unless marked — **(int)** integration.

#### Router loses its branch

- [ ] a final reply routes to `done` even with documents indexed and no tool called
- [ ] a tool-calling reply still routes to `tools`, and still raises `ToolLoopLimitError`
      at the budget
- [ ] `Router` takes `max_tool_rounds` alone — nothing tells it whether the app is grounded

#### The graph is two nodes

- [ ] `langgraph_for` builds from prepare, model, tools and router alone; a `ground` step
      is not a parameter it accepts
- [ ] over fake steps, `run` walks prepare → model → tools → model → done, visiting no
      third node

#### `Agent` stops holding an answer back

- [ ] an `AdapterError` from any step propagates out of `answer` — no held answer is
      returned in its place
- [ ] a turn's trace carries no reconsideration step, and `SecondLookLost` no longer exists
      as a kind

#### Plugins stop declaring a domain

- [ ] `Plugin` has no `scope`, and `PluginSet` exposes none
- [ ] the shipped fitness plugin still contributes its instructions, tools and safety rule
- [ ] the shipped security plugin still contributes its rules and nothing else

#### `assemble`

- [ ] the assembled app answers a scripted question end-to-end with no ground step wired
- [ ] **(int)** a document question is answered in one model round after the search tool
      returns

#### Deletions (the suite shrinks; no test of their own)

- [ ] `tests/acceptance/test_grounding.py` is gone, with the 30 grounding tests spread
      across `test_steps.py`, `test_agent.py`, `test_langgraph_runner.py`,
      `test_assembly.py`, `test_plugin_composition.py` and `test_conversation.py`
- [ ] `test_chroma_retriever.py:43` and `langgraph_runner.py:58` no longer explain
      themselves by naming the gate
