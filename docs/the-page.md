# How the page is built

One React app over cora's own HTTP API, served as static files by the same process that
answers them. What it cannot do, cora cannot be asked to do from a browser — the
[Telegram bot](how-to/run-the-telegram-bot.md) is the same app reached from a chat, and
has a shorter list of its own.

## Where state lives

Three places, and the split is who owns the truth.

- **cora owns the conversation.** Every rail and the transcript read it back through
  `@tanstack/react-query`, one hook per subject under `frontends/react/ui/src/hooks` —
  documents, memory, sessions, plugins, scopes, the pin, the passage a citation points
  at. A delete invalidates the key it wrote to, so the rail redraws from the answer
  rather than from what the page hoped happened.
- **The address owns which conversation.** `frontends/react/ui/src/route.ts` reads the
  thread out of the hash and nothing mirrors it into state, because two answers to "which
  conversation" can disagree and the reader can edit one of them. The hash rather than
  the path: the built page is static with no fallback, so a real path would be a 404 on
  reload.
- **`Page` owns what only a page has.** The open tab, the citation standing over the
  page, the confirmation waiting to be answered, whether a rail is folded, and the last
  thing that went wrong. None of it survives a reload, and none of it needs to.

## Why a column cannot take the page down

Each of the three columns is wrapped in its own `ErrorBoundary`, so a rail that throws
while drawing is replaced by a sentence and the conversation beside it still answers.
Moving to another panel leaves the broken one behind. Whatever threw reaches the console,
which is the only record of it.

## What the API gives it

`frontends/react/src/cora/frontends/react/api.py` is the whole surface: ask and resume,
the documents and their uploads, the sessions and one session's turns, memory, plugins
and scopes. Every route is one thing the page does, and the page holds no cora logic of
its own — it asks, and it draws what came back.

## What holds it

`vitest` over the components and the hooks, `tsc` over the types, and `eslint` with
`frontends/react/ui/scripts/check-styles.mjs` beside it, which fails when a class a
module draws is not declared in the CSS module next to it. The browser tier drives the
real page against a real server and is the only tier that proves the three of them
together.
