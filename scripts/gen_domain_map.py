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
from dataclasses import dataclass
from pathlib import Path

from astroid import nodes
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
# The two colours the component map reads its text in. Written into the DOT because a
# run of text inside an HTML label carries no class of its own — `_classed` turns each
# one back into the class the shared stylesheet names.
STEREOTYPE_INK = "#5f6368"
NAME_INK = "#14425f"


def _compartment(lines: tuple[str, ...]) -> str:
    body = BREAK.join(lines)
    return f'<TR><TD ALIGN="LEFT" BALIGN="LEFT" CELLPADDING="6">{body}{BREAK}</TD></TR>'


def _label(klass: Klass) -> str:
    """One class as the component map draws a component: the stereotype small and grey
    over the name, then a rule under it for each compartment that has anything in it.
    """
    name = f"<I>{klass.name}</I>" if klass.abstract else klass.name
    heading = (
        f'<FONT POINT-SIZE="11" COLOR="{STEREOTYPE_INK}">«{klass.stereotype}»</FONT>'
        "<BR/>"
        if klass.stereotype
        else ""
    )
    rows = [
        f'<TR><TD CELLPADDING="7">{heading}'
        f'<FONT COLOR="{NAME_INK}"><B>{name}</B></FONT></TD></TR>'
    ]
    for lines in (klass.attributes, klass.operations):
        if lines:
            rows.append("<HR/>" + _compartment(lines))
    return (
        '<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="0" CELLPADDING="0">'
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
        f'  graph [fontname="{FONT}", fontsize=11, nodesep=0.5, ranksep=0.7];',
        f'  node [shape=box, style="rounded", margin=0, fontname="{FONT}", '
        "fontsize=12.5, penwidth=1.3];",
        f'  edge [fontname="{FONT}", fontsize=11, labeldistance=1.6, '
        "labelangle=18, penwidth=1.3];",
    ]
    for klass in classes():
        lines.append(f'  "{klass.name}" [label={_label(klass)}, class="uml-class"];')
    lines += [_edge(edge) for edge in edges()]
    lines.append("}")
    return "\n".join(lines) + "\n"


# The component map's own stylesheet, over graphviz's shapes: same typeface, same greys,
# the same white box under the same 1.3px outline, and the same answer to a reader whose
# system asks for a dark page. Sizes are left to the drawing, because graphviz measured
# every box against them — a rule resizing the text would push it out of its own box.
STYLE = """<style>
  text { font-family: -apple-system, "Segoe UI", Roboto, sans-serif; fill: #202124 }
  .stereotype { fill: #5f6368 }
  .name { font-weight: 600; fill: #14425f }
  .uml-class path { fill: #ffffff; stroke: #5f6368; stroke-width: 1.3 }
  .uml-class polygon { fill: #dadce0; stroke: #dadce0 }
  .edge path { fill: none; stroke: #5f6368 }
  .edge text { fill: #6b7280; font-style: italic }
  .uml-specialization polygon,
  .uml-aggregation polygon { fill: #ffffff; stroke: #5f6368 }
  .uml-association polygon,
  .uml-composition polygon { fill: #5f6368; stroke: #5f6368 }
  @media (prefers-color-scheme: dark) {
    text { fill: #e8eaed }
    .stereotype { fill: #9aa0a6 }
    .name { fill: #cfe6f7 }
    .uml-class path { fill: #303134; stroke: #bdc1c6 }
    .uml-class polygon { fill: #5f6368; stroke: #5f6368 }
    .edge path { stroke: #bdc1c6 }
    .edge text { fill: #9aa0a6 }
    .uml-specialization polygon,
    .uml-aggregation polygon { fill: #303134; stroke: #bdc1c6 }
    .uml-association polygon,
    .uml-composition polygon { fill: #bdc1c6; stroke: #bdc1c6 }
  }
</style>"""
DESCRIPTION = (
    "The domain as a UML class diagram: the value objects a turn is made of, their "
    "attributes and operations, a hollow triangle to each parent, a diamond on each "
    "whole that owns its parts, and a role and a multiplicity on every association. "
    "Generated by scripts/gen_domain_map.py."
)
# The white sheet graphviz lays everything on: dropped, so the page shows through.
SHEET = re.compile(r'<polygon fill="white" stroke="none"[^/]*/>\n')
OPENING = re.compile(r"(<svg\b[^>]*>\n)")
# Each run of text inside a label, back to the class that colours it. graphviz writes
# the colour the DOT asked for and no class at all, so the ink identifies the run.
INK = ((STEREOTYPE_INK, "stereotype"), (NAME_INK, "name"))
INKED = re.compile(r'(<text\b[^>]*?) fill="(#[0-9a-f]{6})"')
# The XML prologue and graphviz's own notes about the run, dropped so the file opens on
# the drawing the way the component map does.
PROLOGUE = re.compile(r"\A.*?(?=<svg\b)", re.DOTALL)
SIZED = re.compile(r'(width|height)="([0-9.]+)pt"')


def stamp(source: str) -> str:
    """What the drawing was made from, short enough to read in a diff.

    The rendering is graphviz's and moves with its version; the DOT is this file's and
    moves only with the source. So the stamp is of the DOT, and a guard can tell a
    drawing that is behind the code from one merely drawn by another machine.
    """
    return hashlib.sha256(source.encode()).hexdigest()[:16]


def _classed(drawn: str) -> str:
    named = dict(INK)

    def swap(found: re.Match[str]) -> str:
        head, ink = found.group(1), found.group(2)
        return f'{head} class="{named[ink]}"' if ink in named else found.group(0)

    return INKED.sub(swap, drawn)


def _described(drawn: str) -> str:
    """The drawing announced to a reader who is hearing it rather than seeing it, the
    way the component map announces itself."""
    return OPENING.sub(
        lambda found: found.group(1).replace(
            "<svg ", f'<svg role="img" aria-label="{DESCRIPTION}" ', 1
        ),
        drawn,
        count=1,
    )


def _to_pixels(drawn: str) -> str:
    """The drawing measured the way the component map is measured.

    graphviz sizes the root in points and writes the same numbers into the `viewBox`, so
    a page draws it a third larger than it was laid out — and a third larger than the
    map beside it. Dropping the unit makes one unit one pixel, which is what the numbers
    already say.
    """
    return SIZED.sub(lambda found: f'{found.group(1)}="{found.group(2)}"', drawn, 2)


def svg() -> str:
    source = dot()
    drawn = subprocess.run(
        ["dot", "-Tsvg"], input=source, capture_output=True, text=True, check=True
    )
    out = PROLOGUE.sub("", drawn.stdout, count=1)
    out = _to_pixels(_described(_classed(SHEET.sub("", out))))
    out = OPENING.sub(rf"\1{STYLE}\n", out, count=1)
    drawn_from = f"<!-- drawn by scripts/gen_domain_map.py from {stamp(source)} -->"
    return out.replace("</svg>", f"{drawn_from}\n</svg>")


if __name__ == "__main__":
    MAP.write_text(svg())
    print(f"wrote {MAP.relative_to(ROOT)}")
