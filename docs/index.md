# cora

A RAG chatbot grounded in your own documents: upload them, ask in your own words, and the
agent decides what to look up, which of the domain's tools to run, and what to remember
about you.

This site is for reading the project, not for running it: setup, the gates and the test
tiers stay in the repository's README, which is not part of the site.

## Understand

- [The map](big-picture.md) — the engine, its ports, and the technology behind each one.
  Start here.
- [A session end to end](happy-path.md) — one upload and three questions, drawn as they
  happen.

## Reference

- [`cora.domain`, `cora.ports`, `cora.engine` and `cora.app`](api/index.md) — generated
  from the source, one page per module. These four are what anything outside the app
  imports; `cora.adapters` is not here, because every class in it implements a port and
  its pages would repeat `cora.ports`.
