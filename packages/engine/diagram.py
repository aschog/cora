"""What this package alone is about, so it lives here rather than in scripts/: `make
diagram` finds every `diagram.py` beside a manifest and writes its `diagrams.md`.

The engine is where the contract's shapes are put to work. One picture of the whole
package, kept small by drawing only what a box cannot say for itself: a field and a
signature already name their types, so the only line left is the one nothing writes
down — which port a class could be handed to."""

import uml

PACKAGE = "cora.engine"
CONTRACT = ("cora.domain", "cora.ports")
KINDS = (uml.REALIZATION,)


def render() -> str:
    return uml.digraph("engine", (PACKAGE,), CONTRACT, kinds=KINDS, frame=False)


SECTIONS = (("engine", "The engine, read off the source", "dot", render),)
