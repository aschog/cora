import importlib.util
import pathlib
import shutil
import subprocess
from collections.abc import Callable
from types import ModuleType

import package_diagram
import turn_diagram

Section = tuple[str, str, str, Callable[[], str]]

ROOT = pathlib.Path(__file__).resolve().parent.parent
WORKSPACE = ROOT / "docs" / "diagrams.md"
SPANNING = package_diagram.SECTIONS + turn_diagram.SECTIONS
DRAWN = (
    "`make diagram` draws this into `{name}` beside this page — open that for the"
    " laid-out picture. It is not committed; graphviz draws it again whenever you ask."
)


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


def section(beside: pathlib.Path, entry: Section) -> str:
    """The source is what the page carries, whatever the language. DOT is also drawn:
    graphviz lays it out into an SVG beside the page, which no one commits — a picture
    in the tree would be a second copy of the model to keep true."""
    name, heading, language, render = entry
    source = render()
    written = [f"## {heading}", "", f"```{language}\n{source}\n```"]
    if language != "dot":
        return "\n".join(written)
    picture = beside.parent / f"{name}.svg"
    if shutil.which("dot"):
        subprocess.run(
            ["dot", "-Tsvg", "-o", str(picture)], input=source, text=True, check=True
        )
    return "\n".join([*written, "", DRAWN.format(name=picture.name)])


def page(beside: pathlib.Path, sections: tuple[Section, ...]) -> str:
    drawn = [section(beside, entry) for entry in sections]
    return "\n\n".join(["# Diagrams", *drawn]) + "\n"


if __name__ == "__main__":
    for path, sections in pages().items():
        path.write_text(page(path, sections))
