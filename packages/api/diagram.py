"""What this package alone is about, so it lives here rather than in scripts/: `make
diagram` finds every `diagram.py` beside a manifest and writes its `diagrams.md`.

The picture is read off the classes themselves — imported, then asked for their
annotations — rather than off a rendering of them. So an arrow is a type this package
really declares, and what makes it an arrow is where the type was found: a field or a
property is an association, a parameter or a return is a dependency."""

import importlib
import inspect
import pkgutil
import typing
from collections.abc import Iterable, Iterator, Mapping, Sequence
from typing import Any

PACKAGES = ("cora.domain", "cora.ports")
MANY = (list, tuple, set, frozenset, dict, Sequence, Iterable, Iterator, Mapping)
MULTIPLICITIES = ("1", "0..1", "*")
ASSOCIATION, DEPENDENCY = "-->", "..>"
HEADER = ("  direction LR",)
"""Wide rather than tall: two dozen boxes stack into a column the page has to be
scrolled through otherwise."""


def boxes() -> dict[str, type]:
    """Every class the packages declare, minus the ones that inherit from another of
    them: a subclass says its parent's name and nothing the picture is short of."""
    found: dict[str, type] = {}
    for name in PACKAGES:
        package = importlib.import_module(name)
        for module in pkgutil.iter_modules(package.__path__, f"{name}."):
            members = vars(importlib.import_module(module.name)).items()
            found.update(
                {
                    member.__name__: member
                    for _, member in members
                    if inspect.isclass(member) and member.__module__ == module.name
                }
            )
    declared = set(found.values())
    return {
        name: box for name, box in found.items() if not declared & set(box.__mro__[1:])
    }


def _referenced(annotation: Any, drawn: set[type]) -> list[tuple[type, str]]:
    """The classes an annotation names, each with how many of it the type allows: one
    inside a `tuple` or an `Iterator` is a many, one beside `None` is an optional."""
    if isinstance(annotation, list):
        return [found for one in annotation for found in _referenced(one, drawn)]
    if isinstance(annotation, type) and annotation in drawn:
        return [(annotation, "1")]
    origin = typing.get_origin(annotation)
    if origin is None:
        return []
    arguments = typing.get_args(annotation)
    optional = type(None) in arguments
    many = origin in MANY
    return [
        (
            referenced,
            "*" if many else "0..1" if optional and count == "1" else count,
        )
        for argument in arguments
        if argument is not Ellipsis and argument is not type(None)
        for referenced, count in _referenced(argument, drawn)
    ]


def _annotations(box: type) -> Iterator[tuple[Any, str]]:
    """Where a type was found decides the arrow it draws."""
    for annotation in typing.get_type_hints(box, include_extras=False).values():
        yield annotation, ASSOCIATION
    for name, member in vars(box).items():
        if isinstance(member, property) and member.fget is not None:
            yield typing.get_type_hints(member.fget).get("return"), ASSOCIATION
        elif inspect.isfunction(member) and (
            not name.startswith("_") or name == "__call__"
        ):
            for annotation in typing.get_type_hints(member).values():
                yield annotation, DEPENDENCY


def arrows(drawn: dict[str, type]) -> list[str]:
    edges: dict[tuple[str, str, str], str] = {}
    for name, box in drawn.items():
        for annotation, kind in _annotations(box):
            for referenced, count in _referenced(annotation, set(drawn.values())):
                if referenced is box:
                    continue
                edge = (name, kind, referenced.__name__)
                widest = max([edges.get(edge, "1"), count], key=MULTIPLICITIES.index)
                edges[edge] = widest
    associated = {
        (importer, imported)
        for importer, kind, imported in edges
        if kind == ASSOCIATION
    }
    return [
        f'  {importer} {kind} "{count}" {imported}'
        for (importer, kind, imported), count in sorted(edges.items())
        if kind == ASSOCIATION or (importer, imported) not in associated
    ]


def _folder(box: type) -> str:
    return box.__module__.rsplit(".", 2)[-2]


def grouped(drawn: dict[str, type]) -> list[str]:
    """One namespace per folder the classes were found in, which is the boundary the
    package is built around: what the problem is made of, and the slots it is served
    through."""
    folders = sorted({_folder(box) for box in drawn.values()})
    return [
        line
        for folder in folders
        for line in [
            f"  namespace {folder} {{",
            *(
                f"    class {name}"
                for name, box in drawn.items()
                if _folder(box) == folder
            ),
            "  }",
        ]
    ]


def render() -> str:
    drawn = dict(sorted(boxes().items()))
    return "\n".join(["classDiagram", *HEADER, *grouped(drawn), *arrows(drawn)])


SECTIONS = (("The classes, read off the source", render),)
