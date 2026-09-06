## Why

A plugin doing work of its own leaves nothing on the trace, so a reader watching a turn
sees a call and a silence.

## What Changes

- A plugin says what it just did, in one line, and the reader reads it on the trace
- The line lands under the call it happened inside, beside a delegated loop's rounds
- Cora fills in which plugin said it, so no plugin can sign another's name
- A plugin may mark what it says as having gone wrong, and the trace shows it so
- Said outside a tool call it is dropped, as a step taken outside one already is
- New kind of step, found by the trace the way every other kind is found
- Capability `plugins` gains what a plugin may put on the trace

## Impact

- `src/cora/domain/trace.py` — one more kind of step, named for the plugin that took it
- `src/cora/ports/host.py` — `Host.show`, added surface, so the contract version stands
- `src/cora/engine/host.py` — the plugin's name filled in, and dropped outside a call
- `docs/how-to/write-a-plugin.md`, `README.md` — that a plugin may show its work
- Left alone: the page, which draws any step from the summary and detail it carries
- Left alone: the checkpoint and the conversation store, which find a kind rather than list it
- Left alone: what a handler does, which the trace already names per plugin
- Left alone: `delegate`, which goes on reporting its rounds exactly as it does
