# cora

![CoRa: one core, endless plugin power](docs/assets/hero.png)

On the showcase: [showcase.turingcollege.com](https://showcase.turingcollege.com/).

## Why

An agent that is good at your subject usually means somebody built an app for that
subject. cora turns that around: the agent is the part that stays, and the subject is
the part you write — a fitness coach, a trip, a lab notebook.

## With nothing loaded

It still answers: it searches its documents, remembers what it is told, asks when it
cannot tell, and cites what it used. It changes nothing outside itself unless a plugin
gave it something that does — and then only once you have said yes.

## Start here

- [Get started](docs/how-to/get-started.md) — install, run, gates
- [What cora does](docs/what-it-does.md)
- [What ships with it](docs/what-ships-with-it.md)
- [Write a plugin](docs/how-to/write-a-plugin.md)
- [The docs](docs/index.md) — `make docs` builds them, `make docs-serve` serves them

## Stack

Python 3.12 · [uv](https://docs.astral.sh/uv/) · LangGraph · LangChain over
OpenRouter · SQLite with sqlite-vec · sentence-transformers · React over Starlette.
Gates: ruff, ty and pytest on the Python, eslint, tsc and vitest on the page, and a
browser tier nothing runs for you.
