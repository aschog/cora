## Context

A plugin today has two places to keep something and neither is a file: `State` lasts a
conversation, `Kept` is a row of SQLite. Anything a plugin wants on disk goes through
`POST /api/documents`, which chunks it, embeds it and puts it in the search index — so
the fitness page's workouts are searchable prose, and a vocabulary list would be too. A
field already owns a directory of documents; it owns no directory of its own data.

## Goals / Non-Goals

**Goals:**

- A field keeps named text files that nothing indexes, embeds, searches or cites.
- A plugin reads and writes them as plainly as it reads its store.
- The screen writes one, so a correction made on screen lands without a model in between.
- The files are editable by hand, because the user owns what is in them.

**Non-Goals:**

- Migrating what plugins already keep in documents; fitness stays as it is.
- Binary files, nested directories, or anything the plugin cannot read as text.
- Concurrent-write safety beyond last-writer-wins; one user, one screen.
- Merging on write: whoever writes sends the whole file.

## Decisions

- **A new port beside `Kept`, not a widening of it** — the store is SQLite text by name
  and a file is a file on disk, and a caller has to know which it got.
- **Keyed by field, not by plugin** — the screen addresses a field, a plugin may serve
  two, and documents are already per-field; per-plugin would merge two fields' data.
- **A directory per field under one configured root**, the way `documents_path` already
  works, so moving cora's data means moving directories rather than exporting rows.
- **The port is the seam, the adapter is the extension** — a deployment keeping files
  elsewhere writes another adapter and nothing in `engine` or `ports` moves.
- **Four routes under the field, not one document route with a flag** — a flag on
  `POST /api/documents` would make "is this indexed?" a property of a request rather
  than of a kind of thing.
- **A write replaces the whole file** — appending, de-duplicating and ordering are what
  the data means, and what it means is the plugin's, so the core stays dumb.
- **Listing returns names only** — a caller wanting content reads it by name, and a
  field of large files should not be a single response.
- **`cora.files` follows `cora.documents`**, handed already scoped to the turn, so a
  plugin never names the field it is running in and cannot name another's.

## Risks / Trade-offs

- **A write route is a trust boundary** — the name is validated as one plain segment
  before it touches the filesystem, and a body over the cap is refused with the cap in
  the reason; neither is deferred.
- **Two ways to keep a file now exist**, and a plugin author has to pick; the docs say
  the rule — the user's reading is a document, the plugin's data is a file.
- **Hand-editing races the screen**, and last writer wins; acceptable for one user, and
  the alternative is a lock nobody asked for.
- **Deleting is not asked about here** — the route deletes, and whoever draws a delete
  asks first the way the document rail does, which lands with the screen that offers it.
- **Deleting what is not there is silent**, because a caller retrying a delete wants the
  name gone rather than an error about which attempt won.

## What it touches

- **Ports:** a new `Files` protocol, and `Host` gains `files` beside `store`, over
  the `DirectoryFiles` adapter.
- **Guards:** `tests/guards/test_architecture.py` keeps `ports` free of adapters, and
  the new port under it.
- **Diagrams:** the component map is generated from the composition, so adding an
  adapter and a port redraws it; `scripts/gen_component_map.py` runs unchanged.
- **Docs:** `docs/data-storage.md` gains the directory, and `write-a-plugin.md` the rule
  for choosing between a document and a file.
