# cora

![CoRa: one core, endless plugin power](docs/assets/hero.png)

On the showcase: [cora](https://showcase.turingcollege.com/project/d74b5ac2-789f-485c-ad57-d118f8d4602b).

## Why

An agent that is good at your subject usually means somebody built an app for that
subject. Cora turns that around: the agent is the part that stays, and the subject is
the part you build yourself — a fitness coach, a trip, a lab notebook.

## With nothing loaded

It still answers: it searches its documents, remembers what it is told, asks when it
cannot tell, and cites what it used. It changes nothing outside itself unless a plugin
gave it something that does.

## One cora, many subjects

A plugin's things live in a field of its own. One SQLite file holds cora's own
bookkeeping and partitions a field's vectors apart from every other field's, and
`.cora/documents` is a directory per field holding one Markdown file per upload. A second
subject is a second directory, not a second store — [where your data
lives](docs/data-storage.md) is the whole layout.

## Start here

- [Get started](docs/how-to/get-started.md) — install, run, gates
- [Write a plugin](docs/how-to/write-a-plugin.md)
- [The docs](docs/index.md) — `make docs` builds them, `make docs-serve` serves them

## Stack

Python 3.12 · [uv](https://docs.astral.sh/uv/) · LangGraph · LangChain over
OpenRouter · SQLite with sqlite-vec · sentence-transformers · React over Starlette,
and a Telegram bot beside it.
Gates: ruff, ty and pytest on the Python, eslint, tsc and vitest on the page, and a
browser tier nothing runs for you.
