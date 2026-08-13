"""A UML class diagram in DOT, read off the classes themselves — imported, then asked
for their annotations. What makes a line is where the type was found: a field is an
association, a parameter or a return is a dependency, and a class that answers every
member a Protocol names realizes it. Packages come from the folders.

The subject of a diagram is one distribution's packages; the classes it names in
another are drawn beside it, without members, so a picture stays about its own code."""

import importlib
import inspect
import pkgutil
import re
import typing
from collections.abc import Iterable, Iterator, Mapping, Sequence
from typing import Any

MANY = (list, tuple, set, frozenset, dict, Sequence, Iterable, Iterator, Mapping)
MULTIPLICITIES = ("1", "0..1", "*")
ASSOCIATION, DEPENDENCY, REALIZATION = "association", "dependency", "realization"
STYLES = {
    ASSOCIATION: (),
    DEPENDENCY: ("style=dashed",),
    REALIZATION: ("style=dashed", "arrowhead=empty"),
}
HEADER = (
    "  graph [rankdir=LR, fontname=Helvetica, labeljust=l, ranksep=1.1, pack=true];",
    "  node [shape=box, fontname=Helvetica, margin=0.12];",
    "  edge [fontname=Helvetica, fontsize=10, labelfontsize=9,"
    " labeldistance=2.6, arrowhead=vee];",
)
QUALIFIED = re.compile(r"[A-Za-z_][\w]*\.")


def modules(name: str) -> tuple[str, ...]:
    """A package names its modules; a module names itself, so a diagram can be asked
    for a whole layer or for the two files one subsystem is written in."""
    found = importlib.import_module(name)
    if not hasattr(found, "__path__"):
        return (name,)
    return tuple(
        module.name for module in pkgutil.iter_modules(found.__path__, f"{name}.")
    )


def declared(packages: Iterable[str]) -> dict[str, type]:
    """Every class the modules declare, minus the ones that inherit from another of
    them: a subclass says its parent's name and nothing the picture is short of."""
    found: dict[str, type] = {}
    for name in packages:
        for module in modules(name):
            found.update(
                {
                    member.__name__: member
                    for member in vars(importlib.import_module(module)).values()
                    if inspect.isclass(member) and member.__module__ == module
                }
            )
    inherited = set(found.values())
    return {
        name: box for name, box in found.items() if not inherited & set(box.__mro__[1:])
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
        (referenced, "*" if many else "0..1" if optional and count == "1" else count)
        for argument in arguments
        if argument is not Ellipsis and argument is not type(None)
        for referenced, count in _referenced(argument, drawn)
    ]


def fields(box: type) -> dict[str, Any]:
    return typing.get_type_hints(box, include_extras=False)


def operations(box: type) -> dict[str, Any]:
    """What the class answers to, in declaration order. A Protocol whose whole content
    is `__call__` keeps it — that signature is the port."""
    found = {}
    for name, member in vars(box).items():
        if isinstance(member, property) and member.fget is not None:
            found[name] = typing.get_type_hints(member.fget)
        elif inspect.isfunction(member) and (
            not name.startswith("_") or name == "__call__"
        ):
            found[name] = typing.get_type_hints(member)
    return found


def _annotations(box: type) -> Iterator[tuple[Any, str, str]]:
    """Each type the class writes down, what kind of line it makes, and the name it
    calls it by — a field's name is the association's role, and UML puts that on the
    line rather than in the box, so the type is not written twice."""
    for role, annotation in fields(box).items():
        yield annotation, ASSOCIATION, role
    for name, hints in operations(box).items():
        held = isinstance(vars(box)[name], property)
        for annotation in hints.values():
            yield annotation, ASSOCIATION if held else DEPENDENCY, name if held else ""


def _callables(box: type) -> dict[str, Any]:
    return {
        name: member
        for base in reversed(box.__mro__[:-1])
        for name, member in vars(base).items()
        if inspect.isfunction(member)
    }


def _substitutable(member: Any, required: dict[str, Any]) -> bool:
    """Whether this method could stand in for the one a port declares: the types it
    was promised match, and whatever else it asks for it can do without. Names alone
    are not enough — `add(chunks, vectors, file_hash)` is not `add(chunks)`."""
    hints = typing.get_type_hints(member)
    if any(hints.get(name) != kind for name, kind in required.items()):
        return False
    optional = (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
    return all(
        parameter.default is not inspect.Parameter.empty or parameter.kind in optional
        for name, parameter in inspect.signature(member).parameters.items()
        if name not in required and name != "self"
    )


def realized(box: type, ports: Iterable[type]) -> list[type]:
    """The Protocols this class could be handed to. A Protocol realizes nothing itself,
    and a match is on signatures rather than names: `Step`, `Loader` and `GraphFor` are
    each one `__call__`, and by name alone every callable class would fill all three."""
    if getattr(box, "_is_protocol", False):
        return []
    mine = _callables(box)
    return [
        port
        for port in ports
        if getattr(port, "_is_protocol", False)
        and operations(port)
        and all(
            name in mine and _substitutable(mine[name], required)
            for name, required in operations(port).items()
        )
    ]


def _typed(annotation: Any) -> str:
    """A type as it is written in the source, not as Python repr()s it."""
    if annotation is None or annotation is type(None):
        return "None"
    if isinstance(annotation, type):
        text = annotation.__name__
    else:
        text = QUALIFIED.sub("", str(annotation).replace("typing.", ""))
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _compartment(lines: Iterable[str]) -> str:
    drawn = "<BR/>".join(lines)
    return f'<TR><TD ALIGN="LEFT" BALIGN="LEFT">{drawn}</TD></TR>' if drawn else ""


def _heading(box: type) -> str:
    if getattr(box, "_is_protocol", False):
        return f"&#171;interface&#187;<BR/>{box.__name__}"
    if inspect.isabstract(box):
        return f"<I>{box.__name__}</I>"
    return box.__name__


def label(box: type, members: bool, drawn: Iterable[str] = ()) -> str:
    """The UML class box: what it is, then what it holds, then what it answers to.
    A field that is already a line out of this box is left to the line — writing the
    type in both places says one thing twice. A compartment with nothing left in it is
    left out rather than drawn empty."""
    if not members:
        return f"<{_heading(box)}>"
    held = [
        f"{name} : {_typed(kind)}"
        for name, kind in fields(box).items()
        if name not in drawn
    ]
    answers = [
        f"{name}({', '.join(k for k in hints if k != 'return')})"
        f" {_typed(hints.get('return'))}"
        for name, hints in operations(box).items()
    ]
    return "".join(
        [
            '<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4">',
            f"<TR><TD>{_heading(box)}</TD></TR>",
            _compartment(held),
            _compartment(answers),
            "</TABLE>>",
        ]
    )


def _folder(box: type) -> str:
    return box.__module__.rsplit(".", 2)[-2]


def _box(name: str, box: type, members: bool, roles: Iterable[str]) -> str:
    shown = f"    {name} [label={label(box, members, roles)}"
    return shown + (", shape=plaintext];" if members else "];")


def grouped(
    drawn: dict[str, type],
    subject: set[type],
    members: bool,
    frame: bool,
    roles: Mapping[str, set[str]],
) -> list[str]:
    """One package per folder the classes were found in. Only the subject's own carry
    members; a class from elsewhere is drawn as the name it is referred to by. A page
    already about one subsystem frames only its neighbours — a frame around the subject
    holds it in one block, and the picture grows a column."""
    loose = {n: b for n, b in drawn.items() if not frame and b in subject}
    framed = {n: b for n, b in drawn.items() if n not in loose}
    folders = sorted({_folder(box) for box in framed.values()})
    return [
        *(
            _box(name, box, members and box in subject, roles.get(name, set()))
            for name, box in loose.items()
        ),
        *(
            line
            for folder in folders
            for line in [
                f"  subgraph cluster_{folder} {{",
                f'    label="{folder}";',
                "    labeljust=l;",
                *(
                    _box(name, box, members and box in subject, roles.get(name, set()))
                    for name, box in framed.items()
                    if _folder(box) == folder
                ),
                "  }",
            ]
        ),
    ]


def edges(
    drawn: dict[str, type], subject: set[type], kinds: Iterable[str]
) -> list[tuple[str, str, str, str, str]]:
    """Every line starts at a class the diagram is about: what its neighbours do among
    themselves is their own picture's to say. A picture carrying its members can leave
    the dependencies out — a signature's types are written inside the box already."""
    boxes = set(drawn.values())
    found: dict[tuple[str, str, str, str], str] = {}
    for name, box in drawn.items():
        if box not in subject:
            continue
        for port in realized(box, boxes):
            found[(name, REALIZATION, port.__name__, "")] = ""
        for annotation, kind, role in _annotations(box):
            for referenced, count in _referenced(annotation, boxes):
                if referenced is box:
                    continue
                edge = (name, kind, referenced.__name__, role)
                found[edge] = max(
                    [found.get(edge, "1"), count], key=MULTIPLICITIES.index
                )
    associated = {
        (importer, imported)
        for importer, kind, imported, _ in found
        if kind == ASSOCIATION
    }
    return sorted(
        (importer, kind, imported, role, count)
        for (importer, kind, imported, role), count in found.items()
        if kind in kinds
        and (kind != DEPENDENCY or (importer, imported) not in associated)
    )


def arrows(found: Iterable[tuple[str, str, str, str, str]]) -> list[str]:
    """The role and the multiplicity sit at the end they belong to, which is the end
    the arrow points at: `tool_runtime 1` reads as the one this class calls that."""
    drawn = []
    for importer, kind, imported, role, count in found:
        end = f"{role} {count}".strip()
        shown = [*([f'headlabel="{end}"'] if end else []), *STYLES[kind]]
        drawn.append(f"  {importer} -> {imported} [{', '.join(shown)}];")
    return drawn


def digraph(
    name: str,
    subject: Iterable[str],
    beside: Iterable[str] = (),
    members: bool = True,
    kinds: Iterable[str] = (ASSOCIATION, DEPENDENCY, REALIZATION),
    frame: bool = True,
) -> str:
    """The subject's classes, and beside them the ones they are drawn to — only those,
    so the picture stays the size of what it is about: a neighbour no line reaches is a
    box that says nothing here."""
    own = set(declared(subject).values())
    candidates = dict(sorted({**declared(beside), **declared(subject)}.items()))
    found = edges(candidates, own, kinds)
    touched = {
        name for importer, _, imported, _, _ in found for name in (importer, imported)
    }
    drawn = {n: b for n, b in candidates.items() if b in own or n in touched}
    roles: dict[str, set[str]] = {}
    for importer, kind, _, role, _ in found:
        if kind == ASSOCIATION and role:
            roles.setdefault(importer, set()).add(role)
    return "\n".join(
        [
            f"digraph {name} {{",
            *HEADER,
            *grouped(drawn, own, members, frame, roles),
            *arrows(found),
            "}",
        ]
    )
