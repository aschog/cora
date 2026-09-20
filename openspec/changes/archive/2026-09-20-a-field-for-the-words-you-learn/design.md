## Context

cora holds fields, documents and citations already, and no field is about words. See
proposal.md — Why.

## Goals / Non-Goals

**Goals** — a field whose subject is vocabulary, answering from the lists it holds.

**Non-Goals** — reading a screenshot into a list, which every field wants and so belongs
to cora's own screen. Practising the words. A store of the plugin's own.

## Decisions

**The plugin is instructions and nothing else.**

- Searching the lists is `search_documents`, which every field already has.
- A tool that listed the lists would be a second way to read what the rail shows.
- A page would take the centre and move the conversation into the rail, which is what a
  trainer wants and a vocabulary list does not.

**A list is a Markdown table.**

- A pipe table is unambiguous where a word holds a hyphen or a comma.
- It chunks, embeds, renders in the rail and cites like every other document, with no
  reader of its own.
- The heading carries the language, so one field holds many languages as documents.

## Risks / Trade-offs

- The shape of a list is stated in the instructions rather than enforced → a list
  uploaded in another shape is still searched and cited, only less exactly.
- Until a screenshot can be read, a list arrives by being written or uploaded by hand.

## Ports, guards and diagrams

- No port and no core change: the plugin registers instructions.
- The packaging and architecture guards gain a fifth plugin and its empty import set.
- No diagram changes: nothing about the composition moves.
