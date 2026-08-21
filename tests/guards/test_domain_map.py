"""The domain drawing, checked against the domain.

The map is read out of the source by pyreverse, so what it can go wrong about is what
was left out of it: a class added to `cora.domain` and not drawn, a parent no line runs
to, or a drawing left behind by an edit. Every check reads the committed file — the
rendering needs graphviz, the checks do not.
"""

import ast
import xml.etree.ElementTree as ET

import gen_domain_map as generator
import workspace

MAP = generator.MAP
SVG = "{http://www.w3.org/2000/svg}"
ERRORS = workspace.ROOT / "src" / "cora" / "domain" / "errors.py"


def _classes(path) -> dict[str, tuple[str, ...]]:  # type: ignore[no-untyped-def]
    tree = ast.parse(path.read_text())
    return {
        node.name: tuple(base.id for base in node.bases if isinstance(base, ast.Name))
        for node in tree.body
        if isinstance(node, ast.ClassDef) and not node.name.startswith("_")
    }


def declared() -> dict[str, tuple[str, ...]]:
    """Every class `cora.domain` declares and the map is asked for, off the tree."""
    return {
        name: bases
        for path in sorted(generator.DOMAIN.glob("*.py"))
        if path.name not in generator.NOT_DRAWN
        for name, bases in _classes(path).items()
    }


def _titles(kind: str) -> set[str]:
    root = ET.parse(MAP).getroot()
    return {
        (title.text or "").strip()
        for group in root.iter(f"{SVG}g")
        if kind in (group.get("class") or "").split()
        for title in group.iter(f"{SVG}title")
    }


def drawn_classes() -> set[str]:
    return _titles("node")


def drawn_generalizations() -> set[tuple[str, str]]:
    root = ET.parse(MAP).getroot()
    found = set()
    for group in root.iter(f"{SVG}g"):
        if "uml-specialization" not in (group.get("class") or "").split():
            continue
        for title in group.iter(f"{SVG}title"):
            parent, _, child = (title.text or "").partition("->")
            found.add((child, parent))
    return found


def test_the_map_draws_every_class_the_domain_declares() -> None:
    assert drawn_classes() == set(declared())


def test_the_error_tree_is_left_out() -> None:
    """Twenty-five classes three levels deep, each saying what its parent says: a table
    reads them, a picture only fills up with them."""
    assert drawn_classes() & set(_classes(ERRORS)) == set()


def test_every_parent_in_the_domain_is_drawn_under_its_children() -> None:
    """A generalization is the one relationship a reader is looking for by shape, so a
    subclass whose triangle is missing is a hierarchy the map denies."""
    domain = declared()
    inherited = {
        (child, parent)
        for child, bases in domain.items()
        for parent in bases
        if parent in domain
    }

    assert inherited <= drawn_generalizations()


def test_the_committed_map_is_what_the_generator_writes_today() -> None:
    """The stamp is of the DOT rather than the rendering: a drawing behind the source
    fails here, and one merely drawn by another graphviz does not."""
    assert generator.stamp(generator.dot()) in MAP.read_text(), (
        "the drawing is behind the source it is drawn from: run `make diagram`"
    )


def test_the_map_takes_its_colours_from_the_reader() -> None:
    """graphviz paints black on a white sheet, which is a light page pasted into
    whichever page the reader opened."""
    page = MAP.read_text()

    assert "prefers-color-scheme: dark" in page
    assert 'fill="white"' not in page
