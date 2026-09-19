## Why

A field lists its documents by name, but nothing outside a turn reads one back by that name.

## What Changes

- A document is read back by the name a field lists it under, every upload of it with its text
- A name nothing was uploaded under is answered as not there, and a field nobody loaded is refused
- Capability `documents` — a requirement is added

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `documents`: a document is read back by its name, beside the delete that already takes that name

## Impact

- `src/cora/engine/knowledge_base.py` — answers a name with its uploads' texts
- `frontends/react/src/cora/frontends/react/api.py` — one route beside the delete on the same path
- `tests/cora/engine/test_knowledge_base.py`, `frontends/react/tests/test_api.py` — the new behaviour
- Left alone: the ports, the stores, the listing, the read by upload, and the React page
