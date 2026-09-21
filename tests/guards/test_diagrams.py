"""Every committed drawing, against the source it was drawn from.

By what it contains, never by its bytes. A generated SVG is graphviz's layout, and two
graphviz builds put the same graph at different coordinates and write different
attributes — a byte comparison passes on the machine that drew it and fails on every
other, which is a guard about the developer rather than about the drawing.

So: a class the domain declares is a class the map draws, an interface the composition
root binds is one the map labels, and the steps the walk names are the ones the
sequences show, in that order. What a redraw moves — where a box sits — is exactly what
these do not read.
"""

import ast
import pathlib
import xml.etree.ElementTree as ET

import gen_component_map as components
import gen_domain_map as domain
import sequences
import workspace
from cora.engine.steps import ANSWER, FOCUS, ROUTE, SCREEN, WORK

SVG = "{http://www.w3.org/2000/svg}"


def _text_of(path: pathlib.Path, kind: str) -> set[str]:
    root = ET.parse(path).getroot()
    return {
        (node.text or "").strip()
        for node in root.iter(f"{SVG}text")
        if kind in (node.get("class") or "").split()
    }


def _titles_of(path: pathlib.Path, kind: str) -> set[str]:
    root = ET.parse(path).getroot()
    return {
        (title.text or "").strip()
        for group in root.iter(f"{SVG}g")
        if kind in (group.get("class") or "").split()
        for title in group.iter(f"{SVG}title")
    }


def test_the_component_map_labels_every_interface_the_root_binds() -> None:
    """An interface is a ball and socket rather than a box, so what names it is the text
    beside the connector — and a slot the wiring gained and the drawing did not is the
    map claiming cora has one fewer way to be swapped than it has.
    """
    bound = {binding.port for binding in components.bindings()}

    assert _text_of(components.MAP, "port") == bound


def test_the_component_map_draws_every_frontend_the_workspace_ships() -> None:
    """The map is the answer to "what is cora made of", and a frontend that ships and
    is not on it makes the drawing say there is one fewer way in than there is. Read
    off the manifests rather than a list here, so the next frontend is covered by
    shipping."""
    shipped = {module.rsplit(".", 1)[-1] for _, module in workspace.frontends()}

    assert shipped <= _text_of(components.MAP, "name")


def test_the_domain_map_draws_every_class_the_domain_declares() -> None:
    declared = {
        node.name
        for path in sorted(domain.DOMAIN.glob("*.py"))
        if path.name not in domain.NOT_DRAWN
        for node in ast.parse(path.read_text()).body
        if isinstance(node, ast.ClassDef) and not node.name.startswith("_")
    }

    assert _titles_of(domain.MAP, "node") == declared


def test_the_session_maps_show_the_walk_the_composition_root_names() -> None:
    """The drawing is read for the steps it says a turn takes, and their order:
    screened, then the rounds inside the working step, then answered.
    """
    walk = sequences.walked()
    said = [
        line.receiver
        for line in sequences.flattened(sequences.round_taken().lines)
        if isinstance(line, sequences.Call)
    ]

    assert [name for name, _ in walk.before] == [SCREEN, ROUTE, FOCUS]
    assert walk.marker == WORK
    assert [name for name, _ in walk.after] == [ANSWER]
    assert said.index(SCREEN) < said.index(WORK) < said.index("model")
    assert said.index("model") < said.index(ANSWER)
    # The fork the runner declares at the marker: the rounds are entered only where the
    # opening route says so, and a turn answered before them goes straight on.
    assert said.index(WORK) < said.index("opening") < said.index("model")
    forks = [
        line
        for line in sequences.round_taken().lines
        if isinstance(line, sequences.Fragment) and line.operator == "alt"
    ]
    assert any("opening" in guard for fork in forks for guard, _ in fork.operands)
