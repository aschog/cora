# Big picture

The design is *hexagonal* — ports and adapters. The tests show how the code works;
`docs/sprints/` shows how it was built.

## The map

![cora as a UML component diagram: two frontends, the engine and its parts, nine required
interfaces wired to the components that provide them, and the packages each one depends
on.](assets/component-map.svg)

- Drawn from the source by `scripts/gen_component_map.py`; `tests/guards/test_component_map.py`
  fails if the drawing and `assemble` disagree, or if the committed file is stale.
- Five parts are folded into the ones that hold them: ingestion, the plugin registry,
  citation numbering, `PluginSet`, the tools. What each does and where it lives is in
  [the components](reference/components.md).
- Searching has one path: the tool asks KnowledgeBase, which embeds the question and reads
  the index the uploads went into. Asking several ways is the agent's job, one search per
  trace step.

## The domain

![The domain as a UML class diagram in three columns — what a turn cites, what a turn
records, records and pausing: the value objects a turn is made of, their attributes and
operations, with a hollow triangle to each parent, a diamond on each whole that owns its
parts, and a role and a multiplicity on every association.](assets/domain-map.svg)

- Read out of the classes by `pyreverse` and drawn by graphviz; `scripts/gen_domain_map.py`
  writes it and `tests/guards/test_domain_map.py` fails when the drawing is behind the source.
- The columns are the one thing here no source states — `conversation.py` holds a class from
  two of them — so a guard fails on a class no column claims.
- The `CoreError` tree is left out: 25 classes, three levels, each saying what its parent
  says. It is [a reference table](api/cora/domain/errors/index.md), not a picture.
- A field typed by another drawn class has left its box for the line that carries it, which
  is why some boxes are shorter than the class is.
- `Chunk` is joined to nothing: `cora.ports` wraps it as `RetrievedChunk`, and a port's type
  is not drawn here.
