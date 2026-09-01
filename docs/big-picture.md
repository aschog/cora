# What it is made of

The design is *hexagonal* — ports and adapters. The tests show how the code works;
`docs/sprints/` shows how it was built.

## The map

![cora as a UML component diagram: the React frontend, the engine and its parts, nine
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
