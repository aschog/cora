import grimp
from grimp import ImportGraph

ROOT = "cora"
EXTENSION_POINTS = ("plugins", "frontends")
HEADER = (
    "  graph [rankdir=BT, fontname=Helvetica, labeljust=l, labelloc=b, ranksep=0.7];",
    "  node [shape=tab, fontname=Helvetica, margin=0.16];",
    "  edge [fontname=Helvetica, fontsize=9, fontcolor=gray40,"
    " style=dashed, arrowhead=vee];",
)
"""UML's package: a folder with a tab, and an import drawn the way UML draws one — a
dashed line with an open arrowhead, stereotyped where it points."""


def _is_box(module: str) -> bool:
    parts = module.split(".")
    if len(parts) == 2:
        return parts[1] not in EXTENSION_POINTS
    if len(parts) == 3:
        return parts[1] in EXTENSION_POINTS
    return False


def boxes(graph: ImportGraph) -> tuple[str, ...]:
    return tuple(sorted(module for module in graph.modules if _is_box(module)))


def dependencies(graph: ImportGraph) -> tuple[tuple[str, str], ...]:
    """Squashes the graph in place: each box swallows its own modules, so what is left
    are the imports that cross a boundary."""
    drawn = boxes(graph)
    for box in drawn:
        graph.squash_module(box)
    return tuple(
        sorted(
            (box, imported)
            for box in drawn
            for imported in graph.find_modules_directly_imported_by(box)
            if imported in drawn and imported != box
        )
    )


def _node(box: str) -> str:
    return f'    "{box}" [label="{box.rsplit(".", 1)[-1]}"];'


def grouped(drawn: tuple[str, ...]) -> list[str]:
    """The packages nested the way the namespace nests them: an extension point is a
    package of its own, holding the packages that extend it."""
    nested = {
        point: [box for box in drawn if box.split(".")[1] == point]
        for point in EXTENSION_POINTS
    }
    flat = [box for box in drawn if box.count(".") == 1]
    return [
        f'  subgraph cluster_{ROOT} {{\n    label="{ROOT}";\n    labelloc=b;',
        *(_node(box) for box in flat),
        *(
            line
            for point, boxes_of in nested.items()
            for line in [
                f'    subgraph cluster_{point} {{\n      label="{point}";'
                f"\n      labelloc=b;",
                *(_node(box).replace("    ", "      ", 1) for box in boxes_of),
                "    }",
            ]
        ),
        "  }",
    ]


def diagram(graph: ImportGraph) -> str:
    drawn = boxes(graph)
    arrows = dependencies(graph)
    return "\n".join(
        [
            "digraph packages {",
            *HEADER,
            *grouped(drawn),
            *(
                f'  "{importer}" -> "{imported}" [label="«import»"];'
                for importer, imported in arrows
            ),
            "}",
        ]
    )


def render() -> str:
    return diagram(grimp.build_graph(ROOT))


SECTIONS = (("packages", "The packages, read off the imports", "dot", render),)
