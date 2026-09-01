## Context

Cleaned text is one SQLite blob store shared by every field, and the index holds a second
copy of every passage.

## Goals / Non-Goals

**Goals** — one Markdown file per source, under a directory named for its field. An index
that keeps spans rather than words. A search, a listing and a citation that see one field.
An upload that names the field it lands in, and a page that offers it.

**Non-Goals** — one database for everything, deferred again with pgvector. Moving
remembered facts or threads out of SQLite. Deleting a document, deferred again. A
migration: nothing written before this change is carried over.

## Decisions

**A field is a directory, and a source is a file in it.**

- `<documents root>/<scope>/<stem>-<hash>.md`, the root replacing today's sqlite path.
- The hash in the name is what makes two uploads of one filename two files.
- It is also the index: reading an upload is finding the file whose name carries it.
- Rejected: a manifest per field — a second thing to keep true, where the story asks for one.

**The `Documents` port is asked within a field.**

- `keep` and `read` both take the scope, and a file adapter fills them.
- `SqliteDocuments` goes, with the tests that held it; nothing reads the old store.
- The port already owns "the text a citation opens onto", so the field belongs on it.

**The index keeps a span, and the file keeps the words.**

- A passage is stored as `source`, `index`, `offset`, `length` and its upload — no text.
- `KnowledgeBase` reads each hit's text out of the file its span was measured in.
- A hit whose file is gone is left out rather than handed back empty.
- Cost: a search touches the filesystem once per hit, which is a local read.

**A collection per field, named for it.**

- The directory and the collection carry one name, so a field is one word in two places.
- An empty field is an empty collection, so "nothing uploaded" is true without a filter.
- Rejected: one collection filtered by metadata — a leak is then one missing clause away.

**A passage carries its field, as it already carries its upload.**

- `Chunk` and `Citation` gain the scope, stamped by the index the way the upload is.
- The upload route is asked for a field and an upload, and answers from that field alone.

**The turn's field is ambient, set where every tool call already passes.**

- `ToolRuntime.execute` holds the turn's scopes and binds them for the length of the call.
- That is the pattern `host.py` already uses to bound what a delegated loop may spend.
- `KnowledgeBase.search` reads it, so cora's own tool, `Host.documents` and a delegated
  loop are all scoped by construction.
- Unset means the default field, which is what a bare cora and a bare test both want.
- `ContextSource` keeps its signature, so the plugin contract does not move.
- Rejected: a scope argument on `search` — every plugin would pass a field it cannot see.
- Rejected: binding tools per turn in the tool step — `Host.delegate` would stay unscoped.
- Ingestion stays explicit, because an upload happens outside a turn and names its field.

**An upload names its field, and the door checks the name.**

- `POST /api/documents` takes an optional scope, and absent means the default field.
- The API refuses a field the deployment did not load, naming the ones there are.
- That is also what keeps a name the client chose out of the filesystem.
- The file adapter refuses a scope that is not a bare name, so the check is not the only one.

**The rail offers the field, and lists the one it offered.**

- A pinned thread uploads into its own field; an unpinned one is asked, the default among them.
- A deployment that loaded no fields asks nothing and uses the default.
- The listing takes the same field, so what the page shows is what a turn could cite.

**What moves at the edges.**

- Ports: `documents` and `retrieval` take a field; `context_source`, `plugin` and `host` do not.
- Guards: the component map, redrawn from the assembly; the architecture guard stands.
- Diagrams: the component map, and the sequence that draws a tool call.

## Risks / Trade-offs

- **A hit costs a file read** → local, and the words were a second copy in the index before.
- **A file edited by hand drifts from its offsets** → the directory is cora's to write.
- **One document in two fields is two copies** → a field is meant to be self-contained.
- **The turn's field is implicit** → set in one place, read in one, and the pattern is here already.
- **The upload rail grows a control** → without it a second field is unreachable from the page.
- **Everything already uploaded is lost** → the sprint says nothing is carried over.

## Migration Plan

None: the old store and the old collection are deleted, and the documents re-uploaded.
