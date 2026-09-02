## Why

Every tool cora has reads its own documents, so a question about today earns a polite
refusal.

## What Changes

- The travel scope gains a tool onto a live forecast service, called over HTTP
- A tool declares that what it returns is material cora did not write
- What such a tool returns reaches the model labelled untrusted, as a passage does
- A service that fails or times out costs the turn that call and nothing else
- No citation is handed out for what was fetched, and the trace is the record of the call
- The plugins' technology allow-list widens, keyed per plugin as the frontends' already is
- New capability `live-sources`

## Impact

- `src/cora/ports/plugin.py`, `src/cora/ports/host.py` — a tool declares what its result is
- `src/cora/engine/tool_runtime.py` — a declaring tool's result is labelled where the call is made
- `src/cora/engine/rounds.py` — the label's wording names a service as well as a document
- `plugins/travel/` — new: the forecast tool, and `httpx` declared in its own manifest
- `tests/guards/test_architecture.py`, `tests/guards/test_packaging.py` — a plugin's technology, keyed per plugin and bought by its manifest
- `README.md`, `docs/how-to/write-a-plugin.md` — what travel reaches, and what a tool may declare
- `docs/sprints/5/spec.md` — story 9 leaves it, and the two shapes it does not deliver are recorded
- Left alone: citations, the trace, both serialisation doors, the whole frontend, routing, the pin, memory, and the gate
