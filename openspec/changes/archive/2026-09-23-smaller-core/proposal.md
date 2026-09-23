## Why

Cora's core still holds subjects of its own — documents, memory, and how it asks —
where a plugin could bring each.

## What Changes

- The core's own tools become three over the field's directory: read a file, write one, run a command.
- The two ask tools become a shipped `ask` plugin, over the card hook every gathering tool already has.
- Memory as behaviour becomes a shipped `memory` plugin: the remember tool and the notes in the brief.
- Documents as behaviour becomes a shipped `documents` plugin: reading, chunking, indexing and the search tool.
- **BREAKING** A bare cora reads, writes and runs commands in its field, and nothing else.
- An upload lands as a file of its field, and a new event tells plugins it landed.
- Field files hold bytes as well as text, so a PDF lands where a list does.
- The host hands a plugin an index to put a document into, beside the search it already had.
- A delegated loop is offered the read tool and every system-wide tool that neither acts nor asks.
- A card may say which argument the reader's action lands in, so a fork can be a tool.
- The reading screen asks whether a photo's text is also a document.
- `pypdf` and the search depth setting leave the core with the documents plugin.
- The contract version goes to 2.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `plugins`: the core's three tools, what the host hands over, what a loop is offered, which names are kept, the upload event, the three shipped plugins
- `cards`: asking is the ask plugin's, a card names where the action lands, a fork is put once per conversation
- `documents`: an upload is a file of its field, indexed where the plugin is loaded
- `memory`: the conflict notice moves to the memory plugin's requirements
- `frontend`: the reading screen's checkbox
- `disclosure`: what reaches the model, and what a plugin is handed

## Impact

- `src/cora/engine/ask_tool.py`, `memory_tool.py`, `retrieval_tool.py`, `ingestion.py`, `chunker.py`, `adapters/loaders.py` — leave for the plugins
- `src/cora/engine/steps.py`, `plugin_set.py`, `host.py`, `knowledge_base.py`, `app/assembly.py`, `app/config.py` — lose the ask step, the memory and the search special cases
- `src/cora/engine/field_tools.py`, `ports/shell.py`, `adapters/subprocess_shell.py` — the three tools and the command runner arrive
- `src/cora/domain/trace.py`, `errors.py`, `card.py` — `MemoryUnread` and the ingestion errors leave, an upload refusal and the card's landing name arrive
- `src/cora/ports/host.py`, `files.py`, `graph.py`, `adapters/directory_files.py`, `langgraph_runner.py` — the index, the event, bytes, and a loop without an ask node
- `frontends/react` — the upload route lands a file and dispatches, the reading screen gains a checkbox
- `plugins/ask`, `plugins/memory`, `plugins/documents` — new workspace members, each with its suite
- `pyproject.toml`, `README.md`, the disclosure page, `docs/assets/*.svg` — dependencies, the promise, the diagrams
- `tests/guards` — packaging, installs, diagrams and the front door learn the three members
- Left alone: the gate, citations, the stores and their adapters, the memory rail, the Telegram bot, the cards the page draws
