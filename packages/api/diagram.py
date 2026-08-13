"""What this package alone is about, so it lives here rather than in scripts/: `make
diagram` finds every `diagram.py` beside a manifest and writes its `diagrams.md`."""

import pathlib
import re
import subprocess
import tempfile
from collections.abc import Iterable

NAMESPACE = pathlib.Path(__file__).resolve().parent / "src" / "cora"
GENERATIONS = 0
INHERITS = re.compile(r"^\s*(\w+) --\|> (\w+)$")
NAMES = re.compile(r"\w+")


def classes(packages: Iterable[pathlib.Path], name: str) -> str:
    """pyreverse parses the packages and writes `classes_<name>.mmd` beside a package
    diagram we don't want, so it renders into a directory of its own. One run over them
    all, because a class one package names and another declares is one arrow, and
    `-f OTHER` so that `__call__` counts: a Protocol that is one signature is the whole
    port, and the members are stripped from the picture anyway."""
    with tempfile.TemporaryDirectory() as directory:
        subprocess.run(
            [
                "pyreverse",
                "-f",
                "OTHER",
                "-o",
                "mmd",
                "-p",
                name,
                "-d",
                directory,
                *map(str, packages),
            ],
            check=True,
            capture_output=True,
        )
        return (pathlib.Path(directory) / f"classes_{name}.mmd").read_text().strip()


def _blocks(diagram: str) -> list[list[str]]:
    blocks: list[list[str]] = []
    body: list[str] | None = None
    for line in diagram.splitlines():
        if body is not None:
            body.append(line)
            if line.strip() == "}":
                blocks.append(body)
                body = None
        elif line.strip().startswith("class ") and line.rstrip().endswith("{"):
            body = [line]
        else:
            blocks.append([line])
    return blocks


def _subject(block: list[str]) -> str:
    heading = block[0].strip()
    if not heading.startswith("class "):
        return ""
    return heading.removeprefix("class ").removesuffix("{").strip()


def _generation(name: str, parents: dict[str, str]) -> int:
    generation = 0
    while name in parents:
        name, generation = parents[name], generation + 1
    return generation


def near(diagram: str, generations: int) -> str:
    """A class further than `generations` below the root of its hierarchy goes, and the
    arrow to it with it. At zero the picture is the shapes alone: `CoreError` stands for
    every error and `TraceStep` for every step, which is what their names are for."""
    inheritance = [INHERITS.match(line) for line in diagram.splitlines()]
    parents = {match[1]: match[2] for match in inheritance if match}
    distant = {name for name in parents if _generation(name, parents) > generations}
    kept = [
        block
        for block in _blocks(diagram)
        for edge in [INHERITS.match(block[0])]
        if _subject(block) not in distant
        and not (edge and (edge[1] in distant or edge[2] in distant))
    ]
    return "\n".join(line for block in kept for line in block)


def linked(diagram: str) -> str:
    """pyreverse draws an association from an attribute it sees a body assign, which a
    frozen dataclass and a Protocol never do — so the arrows are read off the member
    lines instead: a class points at every other box its fields or signatures name."""
    blocks = _blocks(diagram)
    drawn = {_subject(block) for block in blocks} - {""}
    edges = sorted(
        {
            (subject, named)
            for block in blocks
            for subject in [_subject(block)]
            if subject
            for line in block[1:]
            for named in NAMES.findall(line)
            if named in drawn and named != subject
        }
    )
    return "\n".join([diagram, *(f"  {a} --> {b}" for a, b in edges)])


def unfilled(diagram: str) -> str:
    """The boxes empty: the members are what the arrows were computed from, and a name
    with the lines it is joined by says more here than ninety fields do."""
    return "\n".join(
        f"  class {_subject(block)}" if _subject(block) else block[0]
        for block in _blocks(diagram)
    )


def render() -> str:
    drawn = classes((NAMESPACE / "domain", NAMESPACE / "ports"), "api")
    return unfilled(linked(near(drawn, GENERATIONS)))


SECTIONS = (("The classes, read off the source", render),)
