# Configuration

Every setting cora reads from the environment, read once at startup by
`app/config.py` and never re-read. A blank is not a value: a variable emptied rather
than unset falls back to its default.

A number that is not a whole number, or is below the minimum named here, stops the app
with one sentence naming the variable — not a traceback out of whatever would have
received it.

## The model

| Setting | What it does | Default |
|---|---|---|
| `OPENROUTER_API_KEY` | The key every request is made with. Required: without it cora does not start. | — |
| `OPENROUTER_BASE_URL` | The OpenAI-style endpoint to call. | `https://openrouter.ai/api/v1` |
| `CORA_MODEL` | Which model answers. `OPENROUTER_MODEL` is read when this is unset, and this one wins whenever both are set. | `openai/gpt-4o-mini` |
| `CORA_MAX_OUTPUT_TOKENS` | The ceiling on one reply, thinking included. Minimum 1. | `8192` |
| `CORA_REQUEST_TIMEOUT` | Seconds to wait for a reply. Minimum 1. | `90` |
| `CORA_REASONING_EFFORT` | How much of that budget a reasoning model may spend thinking: `low`, `medium` or `high`. Sent on every request; a model that does not reason ignores it. | `low` |

## The turn

| Setting | What it does | Default |
|---|---|---|
| `CORA_PLUGINS` | The plugins to load, as module paths separated by commas, in the order they are named. Unset means none: bare cora carries no domain and no screen. | none |
| `CORA_TOP_K` | How many passages one document search returns. Minimum 1. | `5` |
| `CORA_MAX_TOOL_ROUNDS` | How many rounds of tools one turn may spend before the round budget apologises. Minimum 1. | `8` |
| `CORA_HISTORY_TURNS` | How many earlier turns of the thread reach the prompt. `0` means no history. | `20` |

## Where things are kept

Each store is a separate setting, so one can be moved without moving the others.

| Setting | What it does | Default |
|---|---|---|
| `CORA_DB_PATH` | The Chroma index the chunks and their vectors live in. | `.cora/chroma` |
| `CORA_DOCUMENTS_PATH` | The cleaned text a citation opens onto. | `.cora/documents.sqlite` |
| `CORA_MEMORY_PATH` | What is remembered about the user. | `.cora/memory.sqlite` |
| `CORA_CONVERSATIONS_PATH` | Every turn of every conversation. | `.cora/conversations.sqlite` |
| `CORA_LOG_PATH` | Where the log is written. | `.cora/logs/cora.log` |
| `CORA_DEBUG` | `1` or `true` wraps the chat, embedding and retrieval ports in a logger (`cora.engine.port_logging`) that writes one short line each time data crosses one. The engine, the plugins and the frontends do not notice the change. | off |

## The React shell

Read by the server process, not by `app/config.py`.

| Setting | What it does | Default |
|---|---|---|
| `CORA_HOST` | The interface to serve on. | `127.0.0.1` |
| `CORA_PORT` | The port to serve on. Minimum 1. | `8000` |
| `CORA_UI_PATH` | Where the built page is. An installed wheel has no built page beside it, so a deployment that serves one names where it is. Nothing is mounted when the path is absent, which is a dev machine running the page on Vite instead. | `ui/dist` beside the package |
