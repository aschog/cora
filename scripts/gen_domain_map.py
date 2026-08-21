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
# Measured in Georgia, which is the widest of the serifs the stylesheet asks for: a
# reader who has Charter instead gets the same boxes with a little more air in them,
# never a line pushed through its own border.
FONT = "Georgia"
BREAK = '<BR ALIGN="LEFT"/>'

# Every colour the drawing uses, and the class the stylesheet knows it by. A run of text
# or a cell inside an HTML label carries no class of its own, so the colour is what
# `_classed` reads to put one back — which is also why no two of these may be equal.
INK = {
    "name": "#1a1a1a",
    "member": "#33312e",
    "stereotype": "#8a857e",
    "group": "#3f6d94",
    "head": "#f5f4f1",
    "frame": "#c9c6c1",
    "accent": "#2b7fc4",
    "accent-head": "#dceefb",
    "accent-body": "#eff8fe",
    "exception": "#9a3b3b",
    "line": "#5f6368",
}
# The one shape the graph engine and the engine share is drawn as the exception it is.
ACCENTED = "TypedDict"


def _compartment(lines: tuple[str, ...], fill: str) -> str:
    body = BREAK.join(lines)
    tint = f' BGCOLOR="{fill}"' if fill else ""
    return (
        f'<TR><TD ALIGN="LEFT" BALIGN="LEFT" CELLPADDING="7"{tint}>'
        f'<FONT COLOR="{INK["member"]}">{body}{BREAK}</FONT></TD></TR>'
    )


def _label(klass: Klass) -> str:
    """One class in three compartments: the stereotype small and grey over the name on a
    tinted head, then a rule above everything the class declares.

    A `TypedDict` is drawn in the accent colour throughout. It is the one class here
    that is not a value — the state a step returns keys of, and the shape the graph
    engine merges — so the drawing says so before the stereotype is read.
    """
    accented = klass.stereotype == ACCENTED
    frame = INK["accent"] if accented else INK["frame"]
    head = INK["accent-head"] if accented else INK["head"]
    body = INK["accent-body"] if accented else ""
    stereotype_ink = (
        INK["exception"]
        if klass.stereotype == "Exception"
        else INK["accent"]
        if accented
        else INK["stereotype"]
    )
    name = f"<I>{klass.name}</I>" if klass.abstract else klass.name
    heading = (
        f'<FONT POINT-SIZE="10" COLOR="{stereotype_ink}">«{klass.stereotype}»</FONT>'
        "<BR/>"
        if klass.stereotype
        else ""
    )
    rows = [
        f'<TR><TD CELLPADDING="7" BGCOLOR="{head}">{heading}'
        f'<FONT COLOR="{INK["name"]}"><B>{name}</B></FONT></TD></TR>'
    ]
    for lines in (klass.attributes, klass.operations):
        if lines:
            rows.append("<HR/>" + _compartment(lines, body))
    return (
        '<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" CELLPADDING="0" '
        f'COLOR="{frame}">' + "".join(rows) + "</TABLE>>"
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


# What each column of the drawing is for, and which classes answer to it. The one thing
# here that is not read off the source: a reader groups by what a class is *for*, and
# nothing in the code says that — `conversation.py` holds one class from two columns.
# `tests/guards/test_domain_map.py` fails on a class this table forgets, so a domain
# that grows cannot leave a column to be guessed at.
GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "What a turn cites",
        ("Citable", "CitableHits", "Nothing", "Context"),
    ),
    (
        "What a turn records",
        (
            "Turn",
            "ChatResult",
            "AgentState",
            "Citation",
            "TraceStep",
            "ModelDecision",
            "MemoryUnread",
            "ToolUse",
        ),
    ),
    (
        "Records & pausing",
        ("Session", "Chunk", "TurnPaused", "Pending", "Decision", "Option"),
    ),
)


def dot() -> str:
    """The drawing as DOT: every whole above its parts, every parent above its children.

    Each edge is written from the end UML puts the diamond or the triangle on, so the
    layout reads downwards — a turn's result above the passages it cites — and every
    class stands in the column that says what it is for.
    """
    drawn = {klass.name: klass for klass in classes()}
    lines = [
        "digraph domain {",
        "  rankdir=TB;",
        # Right angles, the way a class diagram is drawn by hand. graphviz warns that
        # it does not place edge labels under this router; the roles here are short and
        # land beside the line they belong to, which is what a reader needs of them.
        "  splines=ortho;",
        '  charset="utf-8";',
        '  bgcolor="transparent";',
        f'  graph [fontname="{FONT}", fontsize=10, nodesep=0.55, ranksep=0.75];',
        f'  node [shape=plain, margin=0, fontname="{FONT}", fontsize=12.5];',
        f'  edge [fontname="{FONT}", fontsize=10.5, color="{INK["line"]}", '
        "labeldistance=1.6, labelangle=18, penwidth=1];",
    ]
    for at, (title, members) in enumerate(GROUPS):
        lines += [
            f"  subgraph cluster_{at} {{",
            "    peripheries=0;",
            "    labelloc=t;",
            "    labeljust=l;",
            f'    fontcolor="{INK["group"]}";',
            f'    label="{title.upper()}";',
        ]
        lines += [
            f'    "{name}" [label={_label(drawn[name])}, class="uml-class"];'
            for name in members
            if name in drawn
        ]
        lines.append("  }")
    lines += [_edge(edge) for edge in edges()]
    lines.append("}")
    return "\n".join(lines) + "\n"


# The typeface, and the same drawing for a reader whose system asks for a dark page.
# Every colour is on the shapes already, so this restates only what has to change —
# and never a size, because graphviz measured every box against the ones it was given.
STYLE = """<style>
  text { font-family: Charter, Georgia, "Times New Roman", serif }
  .group { letter-spacing: .12em }
  .edge text { font-style: italic }
  @media (prefers-color-scheme: dark) {
    .name { fill: #e8eaed }
    .member { fill: #d2cec8 }
    .stereotype { fill: #9c968e }
    .group { fill: #7fb0d8 }
    .head { fill: #2b2c2f }
    .frame { stroke: #5f6368 }
    .rule { fill: #5f6368; stroke: #5f6368 }
    .accent { stroke: #6fb6ea }
    .accent-rule { fill: #6fb6ea; stroke: #6fb6ea }
    .accent-head { fill: #16354b }
    .accent-body { fill: #101f2b }
    .accent-ink { fill: #6fb6ea }
    .exception { fill: #d98a8a }
    .edge path { stroke: #bdc1c6 }
    .edge text { fill: #9aa0a6 }
    .edge polygon[fill="none"] { stroke: #bdc1c6 }
    .edge polygon:not([fill="none"]) { fill: #bdc1c6; stroke: #bdc1c6 }
  }
</style>"""
DESCRIPTION = (
    "The domain as a UML class diagram in three columns — what a turn cites, what a "
    "turn records, records and pausing: the value objects a turn is made of with their "
    "attributes and operations, a hollow triangle to each parent, a diamond on each "
    "whole that owns its parts, and a role and a multiplicity on every association. "
    "Generated by scripts/gen_domain_map.py."
)
# The white sheet graphviz lays everything on: dropped, so the page shows through.
SHEET = re.compile(r'<polygon fill="white" stroke="none"[^/]*/>\n')
OPENING = re.compile(r"(<svg\b[^>]*>\n)")
# Every shape and every run of text, back to the class that names it. graphviz writes
# the colour the DOT asked for and no class at all, so the colour is the only handle
# there is — read off `fill` for what is painted and `stroke` for what is drawn.
PAINTED = {ink: name for name, ink in INK.items()}
# A rule and an outline are both drawn in the frame colour; what tells them apart is
# that a rule is filled with it and an outline is not.
STROKED = {INK["frame"]: "rule", INK["accent"]: "accent-rule"}
OUTLINED = {INK["frame"]: "frame", INK["accent"]: "accent"}
INKED = re.compile(r"<(text|polygon)\b[^>]*?>")
ATTRIBUTE = re.compile(r'(fill|stroke)="([^"]+)"')
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


def _class_of(painted: str, stroked: str) -> str:
    """What this shape is, read off the colours it was drawn in.

    The accent ink names a colour rather than a part, so a run of text carrying it is
    the accented class's own writing: `accent-ink`, which the dark page recolours with
    the rest of that box.
    """
    if painted == INK["accent"] and not stroked:
        return "accent-ink"
    if painted in PAINTED and painted != stroked:
        return PAINTED[painted]
    if painted == stroked:
        return STROKED.get(painted, "")
    if painted == "none":
        return OUTLINED.get(stroked, "")
    return ""


def _classed(drawn: str) -> str:
    def swap(found: re.Match[str]) -> str:
        element = found.group(0)
        attributes = dict(ATTRIBUTE.findall(element))
        name = _class_of(attributes.get("fill", ""), attributes.get("stroke", ""))
        if not name:
            return element
        closing = "/>" if element.endswith("/>") else ">"
        return f'{element[: -len(closing)]} class="{name}"{closing}'

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
