import xml.etree.ElementTree as ET

import gen_component_map as generator
import workspace

MAP = generator.MAP
SVG = "{http://www.w3.org/2000/svg}"


def bound_ports() -> set[str]:
    return {binding.port for binding in generator.bindings()}


def drawn_ports() -> set[str]:
    """Every port the drawing labels. A port is a ball and socket, not a box, so what
    names it is the text beside the connector."""
    root = ET.parse(MAP).getroot()
    return {
        (node.text or "").strip()
        for node in root.iter(f"{SVG}text")
        if "port" in (node.get("class") or "").split()
    }


def test_the_map_draws_every_port_the_composition_root_binds() -> None:
    assert drawn_ports() == bound_ports()


def test_the_committed_map_is_what_the_generator_writes_today() -> None:
    assert MAP.read_text() == generator.svg(), (
        "the drawing is behind the source it is drawn from: run `make diagram`"
    )


def test_the_page_shows_the_map_it_references() -> None:
    page = (workspace.ROOT / "docs" / "big-picture.md").read_text()
    reference = f"assets/{MAP.name}"
    assert reference in page, f"big-picture.md does not show {reference}"
