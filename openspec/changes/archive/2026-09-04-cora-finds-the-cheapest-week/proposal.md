## Why

cora can say what a trip should look like, but not what it costs, so a budget is a
question it cannot answer.

## What Changes

- The travel scope gains two tools onto a live search service: flights, and hotels
- A month range and a trip length are asked as such, so a flexible window is one search
- The three cheapest options come back for each half, priced and dated
- A budget and a restriction are search parameters, so a rejected option is never shown
- The service needs a key, which the plugin reads from its own slice of the environment
- Without that key the two tools are not registered, as saving is not offered without an output
- What comes back is untrusted and earns no citation, as the forecast already does
- A service that fails costs the turn that call and nothing else
- Modified capability `live-sources`

## Impact

- `plugins/travel/src/cora/plugins/travel/trips.py` — new: one client, two tools over it
- `plugins/travel/src/cora/plugins/travel/__init__.py` — registers the pair where a key is set
- `plugins/travel/tests/travel/` — new `test_trips.py`, and `test_plugin.py` for the key's absence
- `docs/privacy-and-ethics.md` — a second host, and the first that is told where you want to go
- `README.md`, `docs/how-to/write-a-plugin.md` — what travel reaches, and a plugin holding a credential
- Left alone: the core, every port, the gate, citations, routing, the pin, memory, the frontend
- Left alone: `httpx` and the technology allow-list, both already bought by the forecast
