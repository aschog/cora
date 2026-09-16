# cora

cora is a core that runs a turn: it screens what you asked, searches your documents,
remembers what you tell it, asks when it cannot tell, and cites what it used. Everything
else arrives as a plugin, which registers three kinds of thing — tools, instructions and
a handler at a named point in the turn — each under a field of its own or in every turn.
What a plugin may not have is [what cora enforces whatever a plugin
does](privacy-and-ethics.md#what-loading-a-plugin-costs-in-trust).

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
- [What ships with it](what-ships-with-it.md) — the four plugins in this repository,
  and what each one brings.
- [How the page is built](the-page.md) — the React frontend: who owns which state,
  and why a broken rail leaves the conversation standing.
- [Where your data lives](data-storage.md) — one SQLite file, the documents beside it,
  and what deleting takes.
- [Privacy, and what a plugin costs in trust](privacy-and-ethics.md) — what leaves your
  machine, what is kept where, where the safeguards stop, and what loading someone
  else's code buys them.

## How-to

One task each, for when you are already working.

- [Get started](how-to/get-started.md) — install it, run it, and run the gates it is
  held to
- [Load plugins](how-to/load-plugins.md) — the folder cora reads, and its rules
- [Write a plugin](how-to/write-a-plugin.md) — a persona, tools and a hand in the turn,
  as a file you drop in the folder
- [Run the React shell](how-to/run-the-react-shell.md) — the same app over HTTP, with a
  React page
- [Run the Telegram bot](how-to/run-the-telegram-bot.md) — the same app in a chat, for
  the machine you are not sitting at
- [Watch a turn happen](how-to/watch-a-turn.md) — the trace, the port log, and the live
  session test

## Reference

The facts, as the source states them.

- [`cora.domain`](api/cora/domain/index.md), [`cora.ports`](api/cora/ports/index.md),
  [`cora.engine`](api/cora/engine/index.md) and [`cora.app`](api/cora/app/index.md) —
  generated from the source by `scripts/gen_reference.py`, one page per module. These four are what anything outside
  the app imports; `cora.adapters` is not here, because every class in it implements a
  port and its pages would repeat `cora.ports`.

## Process

Not pages of this site: [the TDD workflow](https://github.com/TuringCollegeSubmissions/gwirte-AE.AFA.4.6/blob/main/docs/workflow.md)
this was built with, and the sprint briefs under `docs/sprints/`. They record how cora
was built rather than what it does.
