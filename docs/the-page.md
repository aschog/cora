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

## Where a document is added

Two controls, one upload. The documents rail carries **Add a document**, standing over
the list it changes, and the composer carries a ＋ beside the question being typed. Both
call the same hook, so a file lands in the same field, the list changes once, and a
refusal is reported in one place — the notice over the rail's list. While an upload is
running the composer's control says so and takes no second file: an upload is seconds of
real indexing, and a reader whose rail is folded has nothing else that would say.

A **photo** added there is read before it is kept. `frontends/react/ui/src/reading.ts`
fetches Tesseract compiled to WebAssembly from `cdn.jsdelivr.net` the first time one is
added — the script, its core and the German and English trained data, pinned and then
cached — and runs it in the browser, so the image is never uploaded. What it recognised
is put up in a dialog to correct, and only what the reader keeps is uploaded, as a
Markdown document named after the photo. Discarding keeps nothing. A photo with no text
in it and a reading that could not be run are two different sentences, because they send
the reader to fix two different things.

## A page a plugin brought

A plugin may register a directory as the page of one field, and the same process serves
it at `/pages/<field>/` — `GET /api/scopes` says which fields have one and where. It is
served on cora's own origin, so it calls the API exactly as this page does and with the
same reach. [Write a plugin](how-to/write-a-plugin.md#a-page) is the contract, and
[privacy](privacy-and-ethics.md#what-loading-a-plugin-costs-in-trust) is what that costs.
Where such a page is drawn is this shell's own decision, and not something the directory
says. This shell draws it in the middle when the conversation is fixed to its field — pinned,
or the only field there is — and the right rail becomes that conversation's chat: the
sessions panel has two states, the conversation you are in and the list of the others,
with a way back between them. A conversation the rail would chat is marked in that list.
Asking there does not move the panels to the steps, which would take the chat off the
screen. Folding the rail gives the page the whole width. A field with no page, and a
conversation fixed to nothing, are drawn exactly as they were.

## A field's notice

A page reads what the browser can see, and a device beside the reader can see more. So
cora keeps one notice per field — a small JSON object, written to `PUT
/api/scopes/<field>/notice` and read from `GET` on the same path — and stamps it with its
own clock as it arrives, so no writer has to agree with cora about the time. A second
notice replaces the first whole. What a notice means is between whoever writes it and the
page that reads it; cora checks that it is small and an object and nothing further.

It is held in memory for as long as the process runs, so a restart loses it and the page
falls back to what it knows itself. It is what is true now, not a record of what happened
— a writer that posts faster than the page asks loses the notices in between.

The shell watches those notices too, and a field that is written to opens its own newest
conversation — so starting a workout on a watch puts the trainer on the screen wherever
the reader had got to. What the notice *says* is never read: a shell that branched on
`{"workout":"running"}` would be a shell that knows one plugin's vocabulary. The first
answer from a field is a baseline, a notice outliving the page that wrote it, and a field
no conversation is pinned to opens nothing — only a turn writes a pin.

## What holds it

`vitest` over the components and the hooks, `tsc` over the types, and `eslint` with
`frontends/react/ui/scripts/check-styles.mjs` beside it, which fails when a class a
module draws is not declared in the CSS module next to it. The browser tier drives the
real page against a real server and is the only tier that proves the three of them
together.
