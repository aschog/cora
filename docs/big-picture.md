# Big picture

cora's engine, its nine ports, and the technology behind each. The design is *hexagonal*
(ports and adapters). The tests show how the code works; `docs/sprints/` shows how it was
built.

## The map

![cora as a UML component diagram: two frontends, the engine and its parts, nine required
interfaces wired to the components that provide them, and the packages each one depends
on.](assets/component-map.svg)

- Drawn from the source by `scripts/gen_component_map.py`; `tests/guards/test_component_map.py`
  fails if the drawing and `assemble` disagree, or if the committed file is stale.
- Sixteen parts, eleven on the map — the other five are drawn inside another part:
  ingestion, the plugin registry, citation numbering, `PluginSet`, the tools. Each one's job
  and file: [the components](reference/components.md).
- Search has one path: the tool asks KnowledgeBase, which embeds the question and reads the
  index the uploads went into. Asking several ways is the agent's job, one search per trace step.

## The domain

![The domain as a UML class diagram in three columns — what a turn cites, what a turn
records, records and pausing: the value objects a turn is made of, their attributes and
operations, with a hollow triangle to each parent, a diamond on each whole that owns its
parts, and a role and a multiplicity on every association.](assets/domain-map.svg)

- Read out of the classes by `pyreverse` and drawn by graphviz; `scripts/gen_domain_map.py`
  writes it and `tests/guards/test_domain_map.py` fails when the drawing is behind the source.
- Read top down: a whole stands above its parts, a parent above its children.
- Three columns, by what a class is *for*. That is the one thing here no source states —
  `conversation.py` holds a class from two of them — so a guard fails on a class no column
  claims.
- The `CoreError` tree is left out — 25 classes, three levels, each saying what its parent
  says. It is [a reference table](api/cora/domain/errors/index.md), not a picture.
- An attribute typed by another class is drawn as the association it is, so it is stated
  once: on the line, with its role and multiplicity.
- `Chunk` stands alone because nothing in the domain holds one: `cora.ports` wraps it as
  `RetrievedChunk`, which is a port's type and not drawn here.
