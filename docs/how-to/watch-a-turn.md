# Watch a turn happen

Three ways to see what cora did, from the cheapest to the most real.

## Read the trace on the page

Every turn carries its trace, and the page draws it under its *STEPS* tab: what the
model decided, which tool ran with which arguments, and what came back, including a call
that failed. Nothing to switch on.

## Log what crosses a port

`CORA_DEBUG` wraps the chat, embedding and retrieval ports in a logger that writes one
short line each time data crosses one:

```sh
export CORA_DEBUG=1
make run
```

The lines go to `CORA_LOG_PATH` — `.cora/logs/cora.log` unless you moved it. The engine,
the plugins and the frontends do not notice the change; the wrapper stands around a port
and nothing reads it back.

## Run the session the drawings are about

[What happens when you ask](../happy-path.md) draws what the code does; this test is what
shows it doing it — an upload, three questions and a fact kept. It calls a real model, so
it runs on the `llm` tier and costs what the model costs:

```sh
uv run --env-file .env pytest -m llm -k whole_session
```
