# What it is made of

The design is *hexagonal* — ports and adapters. The tests show how the code works;
`docs/sprints/` shows how it was built.

## The map

![cora as a UML component diagram: the React frontend, the engine and its parts, ten
required interfaces wired to the components that provide them, and the packages each one
depends on.](assets/component-map.svg)

## The domain

![The domain as a UML class diagram in three columns — what a turn cites, what a turn
records, records and pausing: the value objects a turn is made of, their attributes and
operations, with a hollow triangle to each parent, a diamond on each whole that owns its
parts, and a role and a multiplicity on every association.](assets/domain-map.svg)

- The `CoreError` tree is left out: 25 classes under `CoreError`, three levels, each
  saying what its parent says. It is [a reference table](api/cora/domain/errors/index.md), not a picture.

- `Chunk` is joined to nothing: `cora.ports` wraps it as `RetrievedChunk`, and a port's type
  is not drawn here.

## The page

The React app under `frontends/react/ui` is a caller of the API and nothing more. It
imports no Python, holds no rule about a turn, and would be replaced by a second frontend
without the core noticing — which is the claim the map above makes about every adapter,
tested here by the one adapter a person looks at.

Three layers, and the seam between them is what a change has to respect:

- **`src/api.ts` — the wire.** Every endpoint, once, with the types the API answers in.
  Nothing else in the page calls `fetch`, so what cora returns has one place to be parsed
  and one place to be wrong.
- **`src/hooks/*` — what the page knows.** One hook per thing the reader can be looking
  at: the conversation, the documents, the pin, the rails, what is being deleted, which
  passage is open. A hook holds the reads and the invalidation, so a component asks for a
  value rather than for a refresh.
- **`src/components/*` — what it draws.** A component per part of the screen, its styles
  in a CSS module beside it, and no knowledge of how what it draws was fetched.

`App.tsx` composes those and owns the questions the page asks — the prose of each
confirmation lives beside the rails that raise it, because what a delete costs is the
half a reader cannot see for themselves.

**TanStack Query holds the rails**, with retry and refetch-on-focus both off. cora is one
process on the other end of localhost, so a read that failed did not lose a packet, and
redrawing four rails under a reader who is reading them is not a refresh anybody asked
for. What asks for one is a turn, an upload or a delete — an invalidation the hook that
owns the rail names.

**React does not own the answer's DOM.** An answer arrives a token at a time, and
assigning `innerHTML` per token throws away the reader's selection, which makes copying an
answer while it is still being written impossible. `src/patch.ts` reconciles rendered
Markdown into the block that is already drawn, appending to text that only grew. It is the
one place the page reaches past React on purpose, and the reason is in the file.

**The address is a hash, not a path.** The built page is served as static files with no
fallback, so `/c/<id>` asks the server for a file it does not have. A route that only
works when the page was already open is not a route.

**One card draws every stop.** A decision between two remembered facts, an effect waiting
for approval, and a form cora needs filled in reach the page as the same JSON, and
`PauseCard` knows none of the three apart. A field carries the schema it came from and the
control is drawn from that, so a plugin adds a card the page has never seen without a line
of TypeScript changing.

**A column that cannot be drawn is a sentence, not a blank window.** Each of the three
columns is inside an error boundary, with a fourth under the root for what falls between
them.

What the page deliberately has none of: a state manager beside the query cache, a router
library for one hash, and a component library. Four gates hold it — `eslint` with a guard
that every class drawn is declared, `tsc -b`, a `happy-dom` unit tier, and a browser tier
for the two things that need a real cascade and a real selection.
