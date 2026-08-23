"""What kind of page each written page is, checked rather than intended.

The site is sorted the way Diátaxis sorts documentation: the pages under Understand
explain, the pages under How-to instruct, and the pages under Reference state facts. The
guards here hold the two boundaries that go wrong on their own — an instruction written
into an explanation, and a setting that exists in the source and nowhere on the site.
"""

import pathlib
import re

import workspace
from site_config import config, nav_pages

DOCS = workspace.ROOT / "docs"
EXPLANATION = ("big-picture.md", "happy-path.md")
NOT_A_PAGE = ("sprints", "api")

# An instruction tells the reader to run something. Explanation names files and
# settings; it does not hand out commands, and a command is what these read like. A
# command in these pages is backticked or fenced, so the backtick is part of the
# pattern: `make a` is a command and "made a choice" is prose.
INSTRUCTION = re.compile(
    r"(`make [a-z]|`uv run|```(?:sh|bash)|\bexport |[A-Z][A-Z0-9_]{3,}=)"
)


def _sources() -> list[pathlib.Path]:
    roots = [workspace.ROOT / "src", *(member for member in workspace.members())]
    return [
        path
        for root in roots
        for path in sorted(root.rglob("*.py"))
        if "tests" not in path.parts and ".venv" not in path.parts
    ]


def test_an_explanation_page_gives_no_instructions() -> None:
    """An instruction inside an explanation interrupts the argument and hides the
    instruction from the reader looking for one, so the commands live under How-to."""
    found = {
        page: sorted(
            {
                found.group().strip()
                for found in INSTRUCTION.finditer((DOCS / page).read_text())
            }
        )
        for page in EXPLANATION
    }
    assert {page: hits for page, hits in found.items() if hits} == {}


def test_every_written_page_is_in_the_nav() -> None:
    """A page nobody navigates to is a page nobody maintains."""
    nav = nav_pages(config()["nav"])
    written = {
        str(path.relative_to(DOCS))
        for path in DOCS.rglob("*.md")
        if not set(path.relative_to(DOCS).parts) & set(NOT_A_PAGE)
        and path.name != "workflow.md"
    }
    assert sorted(written - set(nav)) == []
