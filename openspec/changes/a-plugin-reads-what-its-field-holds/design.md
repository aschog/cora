## Context

A plugin reaches documents through `cora.documents`, which answers a search and nothing
else. The knowledge base behind it already holds every name, upload and text. See
proposal.md — Why.

## Goals / Non-Goals

**Goals** — a plugin reads every document of its field as text, through the port it
already holds.

**Non-Goals** — parsing, filtering, a path to the directory, or a change to what the rail
shows.

## Decisions

**The listing is a second question on the port a plugin already holds.**

- `ContextSource` grows one method beside `search`, so the host hands nothing new and the
  guide adds one line.
- Rejected: a path to the field's directory, because the host hands ports and never paths.
- A plugin reading files would also know the store's layout, which is the adapter's
  business.
- Rejected: a search with a large `k`, because a listing through a ranking truncates in
  silence.

**A document is its name and its text, one per upload.**

- The name is what the rail shows, and the text is what a citation opens.
- Two uploads of one name are two documents, because a citation's offsets belong to one
  text.
- Names in the order first uploaded and the uploads of one name together, which is
  what the retriever already lists.

**It reads the fields the turn runs in, as search does.**

- The knowledge base asks `here()`, so a plugin's listing and cora's search see one field
  without being handed it.
- Each document says which field it came from, for a turn running in more than one.

**A document whose file is gone is left out.**

- The rule search applies to a passage holds here: what cannot be opened is not offered.

**The answer is labelled untrusted.**

- The host's reading wrapper marks the listing as it marks a search, so the one door stays
  one door.

## Risks / Trade-offs

- A field with many documents is read whole, and the plugin does the narrowing.
- A filter on the port is a later question, asked when a field grows to need one.
- Text is read from disk on every call, cheap at the sizes fields have, with no cache to
  invalidate.

## Ports, guards and diagrams

- Port: `ContextSource` grows one method, and `Retriever` and `Documents` are untouched.
- Guards: the architecture guard holds the new method's docstring, and nothing else
  changes.
- Diagrams: the component map draws ports as boxes, not methods, so nothing regenerates.
