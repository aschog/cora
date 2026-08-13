"""What this package alone is about, so it lives here rather than in scripts/: `make
diagram` finds every `diagram.py` beside a manifest and writes its `diagrams.md`."""

import pathlib
import re
import subprocess
import tempfile

HEADING = "The domain classes, read off the source"
PACKAGE = pathlib.Path(__file__).resolve().parent / "src" / "cora" / "domain"
GENERATIONS = 0
INHERITS = re.compile(r"^\s*(\w+) --\|> (\w+)$")


def classes(package: pathlib.Path, name: str) -> str:
    """pyreverse parses the package and writes `classes_<name>.mmd` beside a package
    diagram we don't want, so it renders into a directory of its own."""
    with tempfile.TemporaryDirectory() as directory:
        subprocess.run(
            ["pyreverse", "-o", "mmd", "-p", name, "-d", directory, str(package)],
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


def render() -> str:
    return near(classes(PACKAGE, "domain"), GENERATIONS)
