"""The domain drawn as a UML class diagram, read out of the source by pyreverse.

pyreverse does the reading — classes, attributes, operations and which relationship each
association is — and the DOT written here says it in UML: a hollow triangle for a
generalization, a diamond for a whole that owns its parts, an open arrow for an
association, each with the role and multiplicity the annotation gives it. The graph is
laid out top down, so a reader starts at what a turn hands back and follows it into the
parts it is made of.
"""

import argparse
import hashlib
import re
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from astroid import nodes
from pylint.pyreverse import inspector
from pylint.pyreverse.diadefslib import DiadefsHandler
from pylint.pyreverse.diagrams import ClassDiagram
from pylint.pyreverse.inspector import Linker, project_from_files

ROOT = Path(__file__).parent.parent
DOMAIN = ROOT / "src" / "cora" / "domain"
MAP = ROOT / "docs" / "assets" / "domain-map.svg"

# The error hierarchy is one tree of 25 classes under `CoreError`, three levels deep. It
# is a reference table, not a picture: drawing it would fill the page with a shape that
# says the same thing at every node.
NOT_DRAWN = ("errors.py",)
CONTAINER = re.compile(r"^(tuple|list|dict|set|frozenset|Annotated)\[")


Assignment = nodes.AssignAttr | nodes.AssignName
Handle = Callable[[Any, Assignment, nodes.ClassDef], None]


def _only_assignments(handle: Handle) -> Handle:
    """pyreverse reads a name off every node it is handed, and astroid hands it an
    `EmptyNode` for a `NamedTuple`'s synthesised attributes — which crashes every
    association pass over `citations.py` (pylint 4.0.7). Its own handlers are declared
    over assignments alone, so anything else is dropped before it reaches them.
    """

    def guarded(self: Any, node: Assignment, parent: nodes.ClassDef) -> None:
        # The annotation is pyreverse's own, and what it is handed is anything astroid
        # put in `instance_attrs` — so the check is over what arrives, not what is
        # declared to.
        if isinstance(node, nodes.AssignAttr | nodes.AssignName):
            handle(self, node, parent)

    return guarded


# A function put where a method was declared: same parameters, and `self` is passed the
# handler it is called on.
inspector.CompositionsHandler.handle = _only_assignments(  # ty: ignore[invalid-assignment]
    inspector.CompositionsHandler.handle
)

CONFIG = argparse.Namespace(
    mode="PUB_ONLY",
    classes=(),
    show_ancestors=None,
    all_ancestors=True,
    show_associated=None,
    all_associated=True,
    module_names=None,
    show_builtin=False,
    show_stdlib=False,
    max_depth=None,
    only_classnames=False,
)


@dataclass(frozen=True)
class Klass:
    """One class as it is drawn: its compartments, and what kind of thing it is."""

    name: str
    stereotype: str
    abstract: bool
    attributes: tuple[str, ...]
    operations: tuple[str, ...]


@dataclass(frozen=True)
class Edge:
    """One relationship, from the class that declares it to the class it names."""

    kind: str
    owner: str
    other: str
    role: str = ""
    multiplicity: str = ""


def diagram() -> ClassDiagram:
    project = project_from_files(
        [str(DOMAIN)], project_name="domain", black_list=NOT_DRAWN
    )
    linker = Linker(project, tag=True)
    found = DiadefsHandler(CONFIG, []).get_diadefs(project, linker)
    # `PackageDiagram` is a `ClassDiagram`, and the package one is drawn already.
    return next(one for one in found if type(one) is ClassDiagram)


def _bases(node: nodes.ClassDef) -> tuple[str, ...]:
    return tuple(base.as_string().rsplit(".", 1)[-1] for base in node.bases)


def _decorators(node: nodes.ClassDef) -> tuple[str, ...]:
    if node.decorators is None:
        return ()
    return tuple(
        one.func.as_string() if isinstance(one, nodes.Call) else one.as_string()
        for one in node.decorators.nodes
    )


# What a reader has to know that the compartments cannot say: a frozen dataclass is a
# value, a TypedDict is a shape a step returns keys of, an exception is thrown.
STEREOTYPES = (
    ("TypedDict", "TypedDict"),
    ("NamedTuple", "NamedTuple"),
    ("Exception", "Exception"),
    ("ABC", "abstract"),
)


def _stereotype(node: nodes.ClassDef) -> str:
    bases = _bases(node)
    for base, drawn in STEREOTYPES:
        if base in bases:
            return drawn
    if any(one == "dataclass" for one in _decorators(node)):
        return "dataclass"
    return ""


def _abstract(node: nodes.ClassDef) -> bool:
    return "ABC" in _bases(node)


def _attribute(drawn: str) -> str:
    """`name : type` as pyreverse renders it, in UML's `+ name: type`."""
    name, _, kind = drawn.partition(" : ")
    return f"+ {name}: {kind}" if kind else f"+ {name}"


def _operation(method: nodes.FunctionDef) -> str:
    returns = method.returns.as_string().rsplit(".", 1)[-1] if method.returns else ""
    arguments = ", ".join(
        argument.name for argument in method.args.args or () if argument.name != "self"
    )
    signature = f"+ {method.name}({arguments})"
    return f"{signature}: {returns}" if returns else signature


def classes() -> tuple[Klass, ...]:
    """Every class drawn, in the order pyreverse read them, each one once.

    An attribute whose type is another drawn class is an association end, and UML states
    a feature once: those leave the compartment for the line that carries them.

    A `NamedTuple` is read twice — once as written and once as `typing` synthesises it —
    and the synthesised one carries no types, so the first reading is the one kept.
    """
    ends = {(edge.owner, edge.role) for edge in edges() if edge.role}
    found: dict[str, Klass] = {}
    for entity in diagram().classes():
        if entity.title in found:
            continue
        node = entity.node
        assert isinstance(node, nodes.ClassDef)
        kept = [
            one
            for one in entity.attrs
            if (entity.title, one.partition(" : ")[0]) not in ends
        ]
        found[entity.title] = Klass(
            name=entity.title,
            stereotype=_stereotype(node),
            abstract=_abstract(node),
            attributes=tuple(_attribute(one) for one in kept),
            operations=tuple(_operation(one) for one in entity.methods),
        )
    return tuple(found.values())


NAME_IN_TYPE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def _multiplicity(kind: str) -> str:
    return "*" if CONTAINER.match(kind) else "1"


def _referenced(kind: str, drawn: frozenset[str]) -> tuple[str, ...]:
    return tuple(
        name for name in dict.fromkeys(NAME_IN_TYPE.findall(kind)) if name in drawn
    )


def edges() -> tuple[Edge, ...]:
    """Every relationship the source declares, each drawn once.

    pyreverse reports the ones it can infer — a field annotated with a class it also
    drew. A field whose type is a container of one is an association too, and the
    annotation is where its multiplicity is written, so those are read off the type.
    """
    drawing = diagram()
    drawn = frozenset(entity.title for entity in drawing.classes())
    found: list[Edge] = []
    for child, parent in sorted(
        (rel.from_object.title, rel.to_object.title)
        for rel in drawing.relationships.get("specialization", ())
    ):
        found.append(Edge("specialization", child, parent))
    inferred = set()
    for kind in ("composition", "aggregation", "association"):
        for rel in drawing.relationships.get(kind, ()):
            owner, other = rel.to_object.title, rel.from_object.title
            role = rel.name or ""
            inferred.add((owner, role))
            found.append(Edge(kind, owner, other, role, "1"))
    for entity in drawing.classes():
        for attribute in entity.attrs:
            role, _, annotation = attribute.partition(" : ")
            if (entity.title, role) in inferred:
                continue
            for other in _referenced(annotation, drawn):
                found.append(
                    Edge(
                        "association",
                        entity.title,
                        other,
                        role,
                        _multiplicity(annotation),
                    )
                )
    return tuple(dict.fromkeys(found))


# UML's own marks, kept out of the strings above so the drawing owns its notation.
ARROWS = {
    "specialization": "dir=back, arrowtail=empty, arrowsize=1.1",
    "composition": "dir=back, arrowtail=diamond",
    "aggregation": "dir=back, arrowtail=odiamond",
    "association": "arrowhead=vee",
}
FONT = "Helvetica"


BREAK = '<BR ALIGN="LEFT"/>'


def _compartment(lines: tuple[str, ...]) -> str:
    cell = f'<TD ALIGN="LEFT" BALIGN="LEFT">{BREAK.join(lines)}{BREAK}</TD>'
    return f"<TR>{cell}</TR>"


def _label(klass: Klass) -> str:
    name = f"<I>{klass.name}</I>" if klass.abstract else klass.name
    heading = f"«{klass.stereotype}»<BR/>" if klass.stereotype else ""
    rows = [f"<TR><TD><B>{heading}{name}</B></TD></TR>"]
    for lines in (klass.attributes, klass.operations):
        if lines:
            rows.append(_compartment(lines))
    return (
        '<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="6">'
        + "".join(rows)
        + "</TABLE>>"
    )


def _edge(edge: Edge) -> str:
    marks = [ARROWS[edge.kind]]
    if edge.role:
        marks.append(f'label="{edge.role}"')
    if edge.multiplicity:
        marks.append(f'headlabel="{edge.multiplicity}"')
    marks.append(f'class="uml-{edge.kind}"')
    other = edge.other if edge.kind != "specialization" else edge.owner
    owner = edge.owner if edge.kind != "specialization" else edge.other
    return f'  "{owner}" -> "{other}" [{", ".join(marks)}];'


def dot() -> str:
    """The drawing as DOT: every whole above its parts, every parent above its children.

    Each edge is written from the end UML puts the diamond or the triangle on, so the
    layout reads downwards — a turn's result at the top, the passages it cites below it.
    """
    lines = [
        "digraph domain {",
        "  rankdir=TB;",
        '  charset="utf-8";',
        f'  graph [fontname="{FONT}", fontsize=11, nodesep=0.45, ranksep=0.6];',
        f'  node [shape=none, fontname="{FONT}", fontsize=11, margin=0];',
        f'  edge [fontname="{FONT}", fontsize=10, labeldistance=1.6, '
        "labelangle=18, penwidth=1.1];",
    ]
    for klass in classes():
        lines.append(f'  "{klass.name}" [label={_label(klass)}, class="uml-class"];')
    lines += [_edge(edge) for edge in edges()]
    lines.append("}")
    return "\n".join(lines) + "\n"


# graphviz paints in black on white. The page it is read on is whichever the reader's
# system asks for, so the colours are taken off the shapes and stated here once.
STYLE = """<style>
  text { fill: #202124 }
  .uml-class polygon { fill: #ffffff; stroke: #5f6368 }
  .edge path { stroke: #5f6368 }
  .edge text { fill: #5f6368; font-style: italic }
  .uml-specialization polygon,
  .uml-aggregation polygon { fill: #ffffff; stroke: #5f6368 }
  .uml-association polygon,
  .uml-composition polygon { fill: #5f6368; stroke: #5f6368 }
  @media (prefers-color-scheme: dark) {
    text { fill: #e8eaed }
    .uml-class polygon { fill: #303134; stroke: #bdc1c6 }
    .edge path { stroke: #bdc1c6 }
    .edge text { fill: #9aa0a6 }
    .uml-specialization polygon,
    .uml-aggregation polygon { fill: #303134; stroke: #bdc1c6 }
    .uml-association polygon,
    .uml-composition polygon { fill: #bdc1c6; stroke: #bdc1c6 }
  }
</style>"""
# The white sheet graphviz lays everything on: dropped, so the page shows through.
SHEET = re.compile(r'<polygon fill="white" stroke="none"[^/]*/>\n')
OPENING = re.compile(r"(<svg\b[^>]*>\n)")


def stamp(source: str) -> str:
    """What the drawing was made from, short enough to read in a diff.

    The rendering is graphviz's and moves with its version; the DOT is this file's and
    moves only with the source. So the stamp is of the DOT, and a guard can tell a
    drawing that is behind the code from one merely drawn by another machine.
    """
    return hashlib.sha256(source.encode()).hexdigest()[:16]


def svg() -> str:
    source = dot()
    drawn = subprocess.run(
        ["dot", "-Tsvg"], input=source, capture_output=True, text=True, check=True
    )
    out = SHEET.sub("", drawn.stdout)
    out = OPENING.sub(rf"\1{STYLE}\n", out, count=1)
    drawn_from = f"<!-- drawn by scripts/gen_domain_map.py from {stamp(source)} -->"
    return out.replace("</svg>", f"{drawn_from}\n</svg>")


if __name__ == "__main__":
    MAP.write_text(svg())
    print(f"wrote {MAP.relative_to(ROOT)}")
