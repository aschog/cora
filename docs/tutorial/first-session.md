# Your first session

Half an hour, one document, and a model you pay for by the token. By the end you will
have uploaded a document, had it answered from, followed a citation back to the passage
it came from, and asked cora to remember something about you.

You need Python 3.12, [uv](https://docs.astral.sh/uv/), and an
[OpenRouter key](https://openrouter.ai/keys).

## 1. Install

```sh
uv sync
```

## 2. Start it with plugins

```sh
export OPENROUTER_API_KEY=sk-or-...        # required (https://openrouter.ai/keys)
export CORA_PLUGINS=cora.plugins.security,cora.plugins.fitness
make run                                   # or: make run-env, to read the key from .env
```

cora loads no plugin unless asked, so the second line is what turns this from a bare
cora into the coaching app with a prompt-injection screen. Drop it to see
what the box does on its own. `make run-env` reads its environment from `.env` instead,
so put `CORA_PLUGINS` there too rather than exporting it.

## 3. Ask it something

Upload a document (txt/md/pdf) in the sidebar, then ask about it — answers cite
the passages they used. Click a `[1]` in an answer and that document opens beside the
chat with the cited passage highlighted; closing it gives the chat its full width back.
The steps appear as cora takes them and stay with the answer under *How I got there*:
what it decided, which tool it ran with which arguments, and what came back. A question
that needs no documents is answered without searching them.

Ask a question the documents can't answer and cora says so rather than filling the gap
from what the model happens to know: with nothing uploaded it asks you for documents,
and with documents that don't cover the question it says that instead. Small talk is
still answered as small talk.

Ask it to remember something — "remember that I train on Tuesdays and Thursdays",
"I'm vegetarian, keep that in mind" — and it keeps that between sessions: the
sidebar's *What I remember* lists every fact it holds, forgets one at a time, or
forgets everything. It only remembers when you ask it to, never on its own judgement,
and each save appears in the trace like any other tool call. The conversation itself
lives as long as the browser session; what is remembered outlives it.

## 4. Try it on the samples

Sample documents for exercising the upload paths (txt, md, and pdf) live in
`samples/`. Upload each one in the sidebar, then ask questions against them —
e.g. "How much protein should I eat?" or "What are common deadlift mistakes?".

## Where to go next

- [A session end to end](../happy-path.md) — the same session as sequence diagrams,
  read out of the code that runs it
- [The map](../big-picture.md) — why cora is built this way
- [Write a plugin](../how-to/write-a-plugin.md) — your own domain instead of the coach
