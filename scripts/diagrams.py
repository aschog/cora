import importlib.util
import pathlib
from types import ModuleType

import package_diagram
import turn_diagram

ROOT = pathlib.Path(__file__).resolve().parent.parent
WORKSPACE = ROOT / "docs" / "diagrams.md"
SOURCES = (package_diagram, turn_diagram)


def _loaded(path: pathlib.Path) -> ModuleType:
    name = f"diagram_{path.parent.relative_to(ROOT).as_posix().replace('/', '_')}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def pages() -> dict[pathlib.Path, tuple[ModuleType, ...]]:
    """A diagram is written where its subject lives: the pictures that span the
    workspace on one page under docs/, and a package's own beside the package,
    contributed by a `diagram.py` there rather than by a list here."""
    own = {
        path.parent / "diagrams.md": (_loaded(path),)
        for path in sorted(ROOT.glob("packages/**/diagram.py"))
    }
    return {WORKSPACE: SOURCES, **own}


def page(sources: tuple[ModuleType, ...]) -> str:
    sections = [
        f"## {source.HEADING}\n\n```mermaid\n{source.render()}\n```"
        for source in sources
    ]
    return "\n\n".join(["# Diagrams", *sections]) + "\n"


if __name__ == "__main__":
    for path, sources in pages().items():
        path.write_text(page(sources))
