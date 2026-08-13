"""What this package alone is about, so it lives here rather than in scripts/: `make
diagram` finds every `diagram.py` beside a manifest and writes its `diagrams.md`.

The engine is where the contract's shapes are put to work, so this is the picture to
read for how the code hangs together: what each class is built with, what it answers
to, and which port it fills. The api's own classes are drawn beside it by name."""

import uml

PACKAGES = ("cora.engine",)
CONTRACT = ("cora.domain", "cora.ports")


def render() -> str:
    return uml.digraph("engine", PACKAGES, CONTRACT)


SECTIONS = (("classes", "The engine, read off the source", "dot", render),)
