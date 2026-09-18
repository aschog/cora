## Why

A field's page is only ever told things by the browser drawing it, so a device
beside the reader has nowhere to say anything.

## What Changes

- Cora keeps one notice per field: a small JSON object, replaced whole by its writer
- A notice is written under the field's name over HTTP, and read back the same way
- Cora stamps a notice with its own clock as it arrives, so no writer states a time
- A notice is held in memory for as long as cora runs, and is gone on a restart
- A field cora does not offer has no notice, to write or to read
- A notice larger than a few kilobytes is refused, and the held one is unchanged
- A field written to by nobody answers that it has no notice, rather than failing
- Capability `frontend` gains the notice, beside the page it is there for
- Not here: what a notice holds, which is the writer's business and the page's
- Not here: reaching cora from another machine, which `CORA_HOST` already decides
- Not here: the watch that is the first writer, which is the next change

## Impact

- `frontends/react/src/cora/frontends/react/api.py` — the notice written, read and bounded
- `frontends/react/tests/react/test_api.py` — the notice's own tests
- `docs/the-page.md` — what a notice is for, and that it is neither kept nor private
- `docs/privacy-and-ethics.md` — a notice is readable by whoever reaches cora
- Left alone: the ports, the engine and the app, a notice being the frontend's own
- Left alone: the Telegram frontend, which draws no page to read one
- Left alone: every other route, and `vite.config.ts`, which proxies `/api` already
