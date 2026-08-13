import pathlib

import grimp
from grimp import ImportGraph

PAGE = (
    pathlib.Path(__file__).resolve().parent.parent / "docs" / "diagrams" / "packages.md"
)
ROOT = "cora"
EXTENSION_POINTS = ("plugins", "frontends")
HEADER = (
    '%%{init: {"flowchart": '
    '{"nodeSpacing": 40, "rankSpacing": 50, "curve": "basis"}}}%%',
    "flowchart BT",
)


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


def diagram(graph: ImportGraph) -> str:
    drawn = boxes(graph)
    arrows = dependencies(graph)
    depended_on = {module for arrow in arrows for module in arrow}
    return "\n".join(
        [
            *HEADER,
            *(f"  {box}" for box in drawn if box not in depended_on),
            *(f"  {importer} --> {imported}" for importer, imported in arrows),
        ]
    )


def render() -> str:
    return diagram(grimp.build_graph(ROOT))


def write(page: pathlib.Path) -> None:
    before, fence, rest = page.read_text().partition("```mermaid\n")
    _, closing, after = rest.partition("```")
    page.write_text(f"{before}{fence}{render()}\n{closing}{after}")


if __name__ == "__main__":
    write(PAGE)
