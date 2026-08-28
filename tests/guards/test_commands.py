"""Two ways a reader ends up typing a command that does not work, each made to fail
here rather than in their terminal.

The first is a page telling them to run `make something` that the `Makefile` no longer
defines — a target renamed or dropped, and the page left behind saying the old name.
The second is `make run` starting anything but the React shell: a second frontend, or
the shell without the page built in front of it, which serves the previous build and
reads as a caching bug.

Neither is a test of what a page *says* — `CLAUDE.md` bars those, and prose is held by
a person reading it. Whether a target exists is a fact about the tree, the same kind of
claim `test_docs.py` makes about a path.
"""

import pathlib
import re

import workspace
from pages import PAGES

MAKEFILE = workspace.ROOT / "Makefile"
REACT_SERVER = "cora.frontends.react.server"

_TARGET = re.compile(r"^([A-Za-z0-9_.-]+)\s*:(?!=)\s*(.*)$")
_ASSIGNED = re.compile(r"^([A-Za-z0-9_]+)\s*:?=\s*(.*)$")
_FENCE = re.compile(r"^\s*```")
_SPAN = re.compile(r"`([^`]+)`", re.DOTALL)
_COMMAND = re.compile(r"\bmake\s+([a-z][a-z0-9-]*)")


class Recipe:
    """One target of the `Makefile`: what it waits for, and what it runs."""

    def __init__(self, prerequisites: str) -> None:
        self.prerequisites = prerequisites.split()
        self.lines: list[str] = []

    @property
    def script(self) -> str:
        return "\n".join(self.lines)


def _recipes() -> dict[str, Recipe]:
    """Every target the `Makefile` defines. A variable assignment is not a target,
    which is what the lookahead past `:=` is for, and a recipe is the tab-indented run
    of lines under the one that named it."""
    found: dict[str, Recipe] = {}
    variables: dict[str, str] = {}
    current: Recipe | None = None
    for line in MAKEFILE.read_text().splitlines():
        if line.startswith("\t"):
            if current is not None:
                current.lines.append(_expanded(line.strip(), variables))
            continue
        current = None
        if line.startswith("#"):
            continue
        assigned = _ASSIGNED.match(line)
        if assigned:
            variables[assigned[1]] = assigned[2].strip()
            continue
        named = _TARGET.match(line)
        if named:
            current = found.setdefault(named[1], Recipe(named[2]))
    return found


def _expanded(line: str, variables: dict[str, str]) -> str:
    """A recipe as make would run it. A guard that read `$(REACT)` would pass while the
    variable pointed anywhere at all, which is the one thing it is asked about."""
    for name, value in variables.items():
        line = line.replace(f"$({name})", value)
    return line


RECIPES = _recipes()


def _commanded(text: str) -> set[str]:
    """The targets a page hands a reader. Two shapes count and one does not: a line of a
    fenced block that runs one, or names one in that line's comment, and a `make x` in
    backticks — while `make it pass` in a sentence, or drawn inside a diagram, hands
    nobody anything."""
    return _in_fences(text) | _in_spans(text)


def _in_fences(text: str) -> set[str]:
    found: set[str] = set()
    fenced = False
    for line in text.splitlines():
        if _FENCE.match(line):
            fenced = not fenced
            continue
        if not fenced:
            continue
        command, _, comment = line.strip().partition("#")
        if command.startswith("make "):
            found.update(_COMMAND.findall(command))
        found.update(_COMMAND.findall(comment))
    return found


def _in_spans(text: str) -> set[str]:
    outside = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    return {
        named
        for span in _SPAN.findall(outside)
        if (named := _named(" ".join(span.split())))
    }


def _named(span: str) -> str:
    command = _COMMAND.fullmatch(span)
    return command[1] if command else ""


def _stale(pages: tuple[str, ...] = PAGES) -> list[str]:
    """Every page that hands a reader a target the `Makefile` does not define."""
    return sorted(
        f"{page}: make {target}"
        for page in pages
        for target in _commanded(pathlib.Path(page).read_text())
        if target not in RECIPES
    )


def test_the_makefile_reader_finds_the_recipes_it_is_given() -> None:
    """A checker over "every target" is only as true as the reader under it: one that
    found nothing would report no stale command and no wrong start, and read as a clean
    bar rather than an empty one."""
    assert "docs" in RECIPES, "a target the file defines"
    assert "mkdocs build" in RECIPES["docs"].script, "with the line it runs"
    assert RECIPES["ui-build"].prerequisites == [], "a target that waits for nothing"
    assert "APP" not in RECIPES, "a variable is not a target"
    assert "no-such-target" not in RECIPES


def test_the_start_command_starts_the_shell() -> None:
    assert REACT_SERVER in RECIPES["run"].script, (
        "`make run` does not start the React shell, the one command the docs give"
    )
    assert REACT_SERVER in RECIPES["run-env"].script


def test_no_recipe_starts_a_second_frontend() -> None:
    reaching = sorted(
        target for target, recipe in RECIPES.items() if "streamlit" in recipe.script
    )

    assert reaching == [], f"these targets still start Streamlit: {reaching}"


def test_the_start_command_builds_the_page_before_serving_it() -> None:
    """The server reads `frontends/react/ui/dist` and nothing else, so a `run` that
    skipped the build would serve yesterday's page and read as a caching bug."""
    assert "ui-build" in RECIPES["run"].prerequisites
    assert "ui-build" in RECIPES["run-env"].prerequisites


def test_every_command_the_docs_give_is_a_command_the_repository_has() -> None:
    stale = _stale()

    assert stale == [], "\n".join(["pages give targets that do not exist:", *stale])


def test_a_page_naming_a_target_the_repository_dropped_is_named_with_it(
    tmp_path: pathlib.Path,
) -> None:
    page = tmp_path / "stale.md"
    page.write_text("Run it:\n\n```sh\nmake run-on-a-tuesday\n```\n")

    assert _stale((str(page),)) == [f"{page}: make run-on-a-tuesday"]


def test_a_sentence_that_says_make_hands_nobody_a_command() -> None:
    """`docs/workflow.md` says "make it pass" in a sentence and draws it inside a
    diagram. Neither is a command, and a reader who copied one would be typing prose."""
    assert _commanded("Write the minimal code to make it pass.") == set()
    assert _commanded("```\n├─ make it pass\n```") == set()
    assert _commanded("```sh\nmake docs\n```") == {"docs"}
    assert _commanded("```sh\nmake run   # or: make run-env\n```") == {"run", "run-env"}
    assert _commanded("`make diagram` redraws all six") == {"diagram"}
    assert _commanded("`make\ndocs-serve` reads it") == {"docs-serve"}
