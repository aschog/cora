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
CONFIGURATION = DOCS / "reference" / "configuration.md"
NOT_A_PAGE = ("sprints", "api")

# A setting is a literal name in the source, and every one of them is a name a
# deployment can set: `OPENROUTER_API_KEY` is read the same way `CORA_PORT` is.
SETTING = re.compile(r'"((?:CORA|OPENROUTER)_[A-Z0-9_]+)"')
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


def settings() -> set[str]:
    return {name for path in _sources() for name in SETTING.findall(path.read_text())}


def test_the_source_has_settings_to_find() -> None:
    assert len(settings()) > 10, "the extractor found almost none — check the regex"


def test_the_configuration_reference_names_every_setting_the_app_reads() -> None:
    """A setting the source reads and the reference does not name is a setting nobody
    outside the code knows about."""
    page = CONFIGURATION.read_text()
    missing = sorted(name for name in settings() if name not in page)
    assert missing == [], "settings read from the environment but not documented"


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
