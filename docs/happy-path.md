# One session, drawn from the source

Four drawings, each read out of the code it is about by `scripts/gen_session_maps.py`:
a message is a call the method makes, in the order it makes them, and a branch or a loop
in the source is a fragment on the page. `tests/guards/test_session_maps.py` fails when a
drawing is behind what it was read from, or when it names a method nobody answers to.

That the code really runs this way is a test rather than a picture:
`test_a_whole_session_uploads_asks_calculates_and_remembers` in
`tests/acceptance/test_llm_acceptance.py` drives the shipped composition root against a
real model on the `llm` tier — a document in, an answer from it, a plugin's calculation,
and a fact the user asked to be kept. Running it yourself is in
[watch a turn happen](how-to/watch-a-turn.md).

## A document goes in

![A UML sequence diagram of an upload: cora.frontends calls add_file on the knowledge
base, which asks the retriever whether it holds these bytes already, and then either
repairs the text of an upload indexed before any text was kept, or ingests, embeds, keeps
and indexes it.](assets/upload-map.svg)

- The hash comes first, so the same bytes under a second filename cost nothing but the
  lookup — and the branch it opens is the repair, not a shortcut: an upload indexed
  before its text was kept is citable and unopenable until someone uploads it again.
- `ingest` is where a file is rejected — wrong type, over 10 MB, empty after cleaning —
  and where text becomes overlapping chunks. It raises before either write, so a
  document that cannot be read leaves nothing behind.

## A turn, as a frontend asks for one

![A UML sequence diagram of a turn: a frontend calls answer on the agent, the agent runs
the thread on the graph runner, reports each new step to the caller as the states arrive,
asks whether the turn stopped to ask, and records the turn before handing back a
ChatResult.](assets/turn-map.svg)

- Only the question is seeded. The thread carries everything said before it, so a tenth
  turn is opened with its question alone.
- The steps are reported as the states arrive, which is what lets a page show the work in
  progress rather than after it.
- Recording is bookkeeping beside the answer: a store that went away loses the record,
  never the reply.

## A round, as the graph walks it

![A UML sequence diagram of one turn inside the graph: the runner takes the prepare step,
then loops over the model step and the router, and on the router's answer either runs the
round's tools, stops to put a decision to the reader before running them, or leaves the
loop with the answer.](assets/round-map.svg)

- Read off the nodes and edges `LangGraphRunner` declares, so the loop and the three
  routes are the graph's own statement of what a turn is. The engine supplies the steps
  and the one decision; the adapter supplies the graph that walks them.
- The brief is written once, at the top of the turn, which is why the loop reads the
  model and the router only.
- Whether the documents are read is the model's decision, asked for in the brief and
  enforced nowhere.

## The tool that reaches the documents

`ToolStep` never knows which tool it ran. It asks `ToolRuntime` for the name the model
gave, and hands back whatever came out — numbered `[n]` first if the result can cite
itself.

| The model asks for | Which really runs | The trace line the test reads |
|---|---|---|
| `search_documents(query=…)` | `engine/retrieval_tool.py` → `KnowledgeBase.search` | `search_documents(query="…") → n passages from protein.md` |
| `calculate_daily_energy(…)` | `plugins/fitness/tools.py` — Mifflin-St Jeor, scaled by an activity factor | `calculate_daily_energy(sex="male", …) → {"bmr": …, "tdee": …}` |
| `remember(fact=…)` | `engine/memory_tool.py` → the `Memory` port → `adapters/sqlite_store_memory.py` | `remember(fact="is vegetarian") → Remembered: is vegetarian` |

Only the first of the three reaches the documents:

![A UML sequence diagram of a document search: the tool runtime runs the tool, which asks
its context source to search, and the knowledge base embeds the question with the same
embedder the chunks went through and reads the nearest chunks out of the
index.](assets/search-map.svg)

- `context_source` is the knowledge base itself: there is one way to search, and nothing
  sits between the tool and the index the uploads were written to. Asking the question
  several ways is the agent's job, and it shows as another pass through this drawing —
  one search, one trace step.
- `ToolStep` numbers the passages `[n]` against the whole conversation's registry, then
  sends the text on as a tool message labelled untrusted document data.

## What the drawings do not show

**Which way a decision goes.** A fragment says the code can go two ways, never which way
it went. For the one that matters — whether a turn reads the documents at all — read
`test_a_real_model_answers_from_the_documents_but_greets_without_them` in the acceptance
file: a plain domain question and a greeting through one agent, where only the first comes
back with sources.

**Failure.** Every friendly failure — a provider that is down, a tool that raises, a round
budget spent, a store that cannot be reached — is covered at the unit and integration
tiers, where a fake can be made to break on demand. A raise sends no message, so none of
it is drawn here.
