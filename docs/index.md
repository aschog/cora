# cora

cora is an agent you chat with, and plugins give it a scope. It decides for itself what a
turn needs.

The pages are sorted by what you came for.

## Tutorial

- [Your first session](tutorial/first-session.md) — install it, upload a document, follow
  a citation back to the passage it came from, and ask it to remember something

## Understand

Why cora is built the way it is.

- [The map](big-picture.md) — the engine, its nine ports, and what the tests pin down.
  Start here.
- [A session end to end](happy-path.md) — an upload, a turn, a round and a search, read
  out of the methods that take them.

## How-to

One task each, for when you are already working.

- [Write a plugin](how-to/write-a-plugin.md) — a persona, tools and rules, as a package
  to install
- [Add a file format](how-to/add-a-file-format.md) — a loader and a registry entry
- [Swap the technology behind a port](how-to/swap-a-port.md) — a class that fits the
  Protocol, passed to `assemble`
- [Run the React shell](how-to/run-the-react-shell.md) — the same app over HTTP, with a
  React page
- [Run the tests](how-to/run-the-tests.md) — four tiers, and which of them costs money
- [Watch a turn happen](how-to/watch-a-turn.md) — the trace, the port log, and the live
  session test

## Reference

The facts, as the source states them.

- [Configuration](reference/configuration.md) — every setting read from the environment
- [The ports](reference/ports.md) — each surface, and what fills it at startup
- [The components](reference/components.md) — the sixteen parts and what each one does
- [A turn, step by step](reference/a-turn.md) — `answer()` and `add_file()` in order
- [The packages](reference/packages.md) — which distribution to install
- [The HTTP surface](reference/http-api.md) — what the React shell's routes answer
- [`cora.domain`, `cora.ports`, `cora.engine` and `cora.app`](api/index.md) — generated
  from the source, one page per module. These four are what anything outside the app
  imports; `cora.adapters` is not here, because every class in it implements a port and
  its pages would repeat `cora.ports`.
