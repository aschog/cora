# Submission prep

## Code to be able to open and narrate

- `src/cora/engine/steps.py` — `ScreenStep`, `RouteStep`, `FocusStep`, `ModelStep`,
  `ToolStep`, `GateStep`, `AskStep`, `AnswerStep`. Written out in `submission-notes.md`.
- `src/cora/ports/host.py` and `src/cora/ports/plugin.py` — the public contract, and the
  `CONTRACT` version refusal at startup. Written out in `submission-notes.md`.
- `src/cora/engine/removal.py` — deleting a plugin, and how the fields leaving with it are
  worked out when nothing is tagged by plugin. Written out in `submission-notes.md`.
- `src/cora/engine/knowledge_base.py` — `forget(scope, name)`: scope is the partition,
  name is the listed filename, upload is the sha256; passages leave the index before the
  file leaves the directory. Written out in `submission-notes.md`.
- `src/cora/adapters/langgraph_runner.py` — the graph wiring, tool calls routed through
  the gate, and how a parked turn is picked up. Written out in `submission-notes.md`.
- `src/cora/engine/nesting.py` and `src/cora/domain/trace.py` — the nested trace, and why
  a plugin's own loop shows its work. Written out in `submission-notes.md`.

## Said first, not found

Injection screening is still two regexes, and nothing scans a document's text at ingest.
The React page has no heading outline and no tab/panel wiring. There is no retrieval
evaluation set. There is no hosted deployment: `make run` is how it is demonstrated. Code
as cora's subject, and a second frontend, are cuts rather than limits of the contract.
