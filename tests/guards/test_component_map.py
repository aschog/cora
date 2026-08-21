import xml.etree.ElementTree as ET

import gen_component_map as generator
import workspace

MAP = generator.MAP
SVG = "{http://www.w3.org/2000/svg}"


def bound_ports() -> set[str]:
    return {binding.port for binding in generator.bindings()}


def drawn_ports() -> set[str]:
    """Every interface the drawing labels. An interface is a ball and socket, not a box,
    so what names it is the text beside the connector."""
    root = ET.parse(MAP).getroot()
    return {
        (node.text or "").strip()
        for node in root.iter(f"{SVG}text")
        if "port" in (node.get("class") or "").split()
    }


def _boxes(root: ET.Element, *styles: str) -> list[generator.Box]:
    return [
        generator.Box(
            float(node.get("x") or 0),
            float(node.get("y") or 0),
            float(node.get("width") or 0),
            float(node.get("height") or 0),
        )
        for node in root.iter(f"{SVG}rect")
        if set((node.get("class") or "").split()) & set(styles)
    ]


def test_the_map_draws_every_interface_the_composition_root_binds() -> None:
    assert drawn_ports() == bound_ports()


def test_the_committed_map_is_what_the_generator_writes_today() -> None:
    assert MAP.read_text() == generator.svg(), (
        "the drawing is behind the source it is drawn from: run `make diagram`"
    )


def test_a_ball_and_socket_stands_in_the_wire_clear_of_both_components() -> None:
    """An interface is what two components meet at, so its ball reads as neither one's
    own: the glyph stands in the wire, with air on both sides of it.
    """
    root = ET.parse(MAP).getroot()
    components = _boxes(root, "outer", "engine")
    for ball in root.iter(f"{SVG}circle"):
        if "ball" not in (ball.get("class") or "").split():
            continue
        x, y, r = (float(ball.get(name) or 0) for name in ("cx", "cy", "r"))
        for box in components:
            if not box.y - 4 <= y <= box.bottom + 4:
                continue
            gap = min(abs(box.x - (x + r)), abs(box.right - (x - r)))
            assert gap >= 20, (
                f"the ball at {x:g},{y:g} is {gap:g}px from a component — it reads as "
                "that component's own dependency"
            )


def test_every_interface_is_named_beside_the_row_it_is_wired_on() -> None:
    """The name of an interface is read on the row its connector runs along, so it is
    drawn above that wire and not over the box at either end.
    """
    root = ET.parse(MAP).getroot()
    rows = generator.plan().rows
    named = {
        (node.text or "").strip(): float(node.get("y") or 0)
        for node in root.iter(f"{SVG}text")
        if "port" in (node.get("class") or "").split()
    }
    for port, y in rows.items():
        assert 0 < y - named[port] <= 30, f"{port} is not named above its own wire"


def test_the_page_shows_the_map_it_references() -> None:
    page = (workspace.ROOT / "docs" / "big-picture.md").read_text()
    reference = f"assets/{MAP.name}"
    assert reference in page, f"big-picture.md does not show {reference}"
