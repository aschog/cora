# cora

A RAG chatbot grounded in your own documents: upload them, ask in your own words, and the
agent decides what to look up, which of the domain's tools to run, and what to remember
about you.

The pages are sorted by what you came for. Setup and running the app stay in the
repository's README, which is not part of this site.

## Understand

Why cora is built the way it is.

- [The map](big-picture.md) — the engine, its nine ports, and what the tests pin down.
  Start here.
- [A session end to end](happy-path.md) — one upload and three questions, drawn as they
  happen.

## How-to

One task each, for when you are already working.

- [Write a plugin](how-to/write-a-plugin.md) — a persona, tools and rules, as a package
  to install
- [Add a file format](how-to/add-a-file-format.md) — a loader and a registry entry
- [Swap the technology behind a port](how-to/swap-a-port.md) — a class that fits the
  Protocol, passed to `assemble`
- [Watch a turn happen](how-to/watch-a-turn.md) — the trace, the port log, and the live
  session test

## Reference

The facts, as the source states them.

- [Configuration](reference/configuration.md) — every setting read from the environment
- [The ports](reference/ports.md) — each surface, and what fills it at startup
- [The components](reference/components.md) — the sixteen parts and what each one does
- [A turn, step by step](reference/a-turn.md) — `answer()` and `add_file()` in order
- [The packages](reference/packages.md) — which distribution to install
- [`cora.domain`, `cora.ports`, `cora.engine` and `cora.app`](api/index.md) — generated
  from the source, one page per module. These four are what anything outside the app
  imports; `cora.adapters` is not here, because every class in it implements a port and
  its pages would repeat `cora.ports`.
