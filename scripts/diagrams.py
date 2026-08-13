import importlib.util
import pathlib
from collections.abc import Callable
from types import ModuleType

import package_diagram
import turn_diagram

Section = tuple[str, Callable[[], str]]

ROOT = pathlib.Path(__file__).resolve().parent.parent
WORKSPACE = ROOT / "docs" / "diagrams.md"
SPANNING = package_diagram.SECTIONS + turn_diagram.SECTIONS


def _loaded(path: pathlib.Path) -> ModuleType:
    name = f"diagram_{path.parent.relative_to(ROOT).as_posix().replace('/', '_')}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def pages() -> dict[pathlib.Path, tuple[Section, ...]]:
    """A diagram is written where its subject lives: the pictures that span the
    workspace on one page under docs/, and a package's own beside the package,
    contributed by a `diagram.py` there rather than by a list here."""
    own = {
        path.parent / "diagrams.md": _loaded(path).SECTIONS
        for path in sorted(ROOT.glob("packages/**/diagram.py"))
    }
    return {WORKSPACE: SPANNING, **own}


def page(sections: tuple[Section, ...]) -> str:
    drawn = [
        f"## {heading}\n\n```mermaid\n{render()}\n```" for heading, render in sections
    ]
    return "\n\n".join(["# Diagrams", *drawn]) + "\n"


if __name__ == "__main__":
    for path, sections in pages().items():
        path.write_text(page(sections))
