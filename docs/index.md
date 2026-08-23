# cora

cora is an agent you chat with, and plugins give it a scope. It decides for itself what a
turn needs.

The pages are sorted by what you came for.

## Tutorial

- [Your first session](tutorial/first-session.md) — install it, upload a document, follow
  a citation back to the passage it came from, and ask it to remember something

## Understand

Why cora is built the way it is.

- [What it is made of](big-picture.md) — the engine, its nine ports, and what the tests
  pin down. Start here.
- [What happens when you ask](happy-path.md) — an upload, a turn, a round and a search,
  read out of the methods that take them.

## How-to

One task each, for when you are already working.

- [Write a plugin](how-to/write-a-plugin.md) — a persona, tools and rules, as a package
  to install
- [Run the React shell](how-to/run-the-react-shell.md) — the same app over HTTP, with a
  React page
- [Watch a turn happen](how-to/watch-a-turn.md) — the trace, the port log, and the live
  session test

## Reference

The facts, as the source states them.

- [`cora.domain`](api/cora/domain/index.md), [`cora.ports`](api/cora/ports/index.md),
  [`cora.engine`](api/cora/engine/index.md) and [`cora.app`](api/cora/app/index.md) —
  generated from the source, one page per module. These four are what anything outside
  the app imports; `cora.adapters` is not here, because every class in it implements a
  port and its pages would repeat `cora.ports`.
