"""What this package alone is about, so it lives here rather than in scripts/: `make
diagram` finds every `diagram.py` beside a manifest and writes its `diagrams.md`.

The contract is an inventory of shapes and slots, so its classes are drawn by name.
What holds and uses them is `cora.engine`, and that picture is on the engine's page."""

import uml

PACKAGES = ("cora.domain", "cora.ports")


def render() -> str:
    return uml.digraph("classes", PACKAGES, members=False)


SECTIONS = (("classes", "The classes, read off the source", "dot", render),)
