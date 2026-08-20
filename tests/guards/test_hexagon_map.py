import inspect
import typing
import xml.etree.ElementTree as ET

import workspace
from cora.app.assembly import assemble

MAP = workspace.ROOT / "docs" / "assets" / "hexagon-map.svg"
SVG = "{http://www.w3.org/2000/svg}"
# `assemble` takes the factory; the engine holds the runner it returns, and that is the
# port a reader of the map is looking for.
AS_DRAWN = {"GraphFor": "GraphRunner"}
# Two slots the engine talks through that are not arguments to `assemble`: the loader
# registry is fixed at the composition root, and a plugin arrives in the plugin set.
NOT_ARGUMENTS = frozenset({"Loader", "Plugin"})


def _protocols(annotation: object) -> set[str]:
    named = {
        getattr(part, "__name__", "")
        for part in (typing.get_args(annotation) or (annotation,))
    }
    return {name for name in named if name and name != "NoneType"}


def bound_ports() -> set[str]:
    declared = {
        name
        for path in (workspace.ROOT / "src" / "cora" / "ports").glob("*.py")
        for name in (path.read_text(),)
        for name in [line for line in name.splitlines() if line.startswith("class ")]
    }
    in_ports = {line.removeprefix("class ").split("(")[0] for line in declared}
    bound = {
        AS_DRAWN.get(name, name)
        for parameter in inspect.signature(assemble).parameters.values()
        for name in _protocols(parameter.annotation)
    }
    return (bound & (in_ports | set(AS_DRAWN.values()))) | NOT_ARGUMENTS


def drawn_ports() -> set[str]:
    root = ET.parse(MAP).getroot()
    children = list(root)
    found = set()
    for index, node in enumerate(children):
        if node.tag == f"{SVG}rect" and "port" in (node.get("class") or ""):
            label = children[index + 1]
            assert label.tag == f"{SVG}text", "a box is drawn with its label after it"
            found.add((label.text or "").strip())
    return found


def test_the_map_draws_every_port_the_composition_root_binds() -> None:
    assert drawn_ports() == bound_ports()


def test_the_page_shows_the_map_it_references() -> None:
    page = (workspace.ROOT / "docs" / "big-picture.md").read_text()
    reference = f"assets/{MAP.name}"
    assert reference in page, "the map is drawn on the page it explains"
    assert MAP.is_file()


def test_the_ports_table_has_a_row_for_every_port_the_map_draws() -> None:
    page = (workspace.ROOT / "docs" / "big-picture.md").read_text()
    described = {name for name in bound_ports() if f"| **{name}" in page}
    missing = sorted(bound_ports() - described - {"Loader"})
    assert missing == [], "the table calls the loader registry `Loaders`, plural"
