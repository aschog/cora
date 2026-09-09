# cora

cora is a core that runs a turn: it screens what you asked, searches your documents,
remembers what you tell it, asks when it cannot tell, and cites what it used. Everything
else arrives as a plugin — a field, tools, rules, and a say in the steps of a turn. Two
things no plugin may have: the gate an effect waits at, and the label that marks what
cora did not write.

The pages are sorted by what you came for.

## Tutorial

- [Your first session](tutorial/first-session.md) — install it, upload a document, follow
  a citation back to the passage it came from, and ask it to remember something

## Understand

Why cora is built the way it is.

- [What it is made of](big-picture.md) — the engine, its ten ports, and what the tests
  pin down. Start here.
- [What happens when you ask](happy-path.md) — an upload, a turn, a round and a search,
  read out of the methods that take them.
- [What cora does](what-it-does.md) — the fields, the cards, the gate an effect waits
  at, and what deleting any of it takes.
- [What ships with it](what-ships-with-it.md) — the three plugins in this repository,
  and what each one brings.
- [Where your data lives](data-storage.md) — one SQLite file, the documents beside it,
  and what deleting takes.
- [Privacy, and what a plugin costs in trust](privacy-and-ethics.md) — what leaves your
  machine, what is kept where, where the safeguards stop, and what loading someone
  else's code buys them.

## How-to

One task each, for when you are already working.

- [Get started](how-to/get-started.md) — install it, run it, and run the gates it is
  held to
- [Load plugins](how-to/load-plugins.md) — name a module, or drop one in the folder
- [Write a plugin](how-to/write-a-plugin.md) — a persona, tools and a hand in the turn,
  as a package to install
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
