"""The first screen, held to the parts a reader needs before they read any code.

`test_tagline.py` holds the one sentence and `test_docs.py` holds every path the docs
claim. Neither notices when the front door stops saying what problem cora solves, which
is how a reviewer came to read a README that did not convey the idea while the suite was
green. This is the guard that would have failed.

The subject is the first screen — everything above the quick start, which is what a
reader has seen before they are told to install anything. Shape is what is checked and
never wording: a rewrite of the prose has to be free, and a part going missing must not
be.
"""

import pytest

import workspace

README = workspace.ROOT / "README.md"
QUICK_START = "## Quick start"

PURPOSE = "## What it is for"
MECHANISM = "## How it works"
EXTENDING = "## Writing your own plugin"
ABSENCES = "## What cora does not have"
HOW_TO = "docs/how-to/write-a-plugin.md"
SHOWCASE = "showcase.turingcollege.com"


def first_screen() -> str:
    """Everything above the quick start."""
    return README.read_text().split(QUICK_START)[0]


def sections() -> dict[str, str]:
    """The first screen's headings, each against the text under it. A part that is a
    heading and nothing else is not a part, so the body is what gets asserted on."""
    found: dict[str, str] = {}
    heading = ""
    for line in first_screen().splitlines():
        if line.startswith("## "):
            heading = line.rstrip()
            found[heading] = ""
        elif heading:
            found[heading] += line + "\n"
    return found


@pytest.mark.xfail(strict=True, reason="story 1: the first screen is not written yet")
def test_the_front_door_explains_itself() -> None:
    """The acceptance criterion, as one test: a stranger reading only this much can say
    what cora is for, how it works, what extending it involves and what it will not do —
    and can reach the showcase entry and the plugin how-to from here."""
    screen = first_screen()

    missing = [
        part
        for part in (PURPOSE, MECHANISM, EXTENDING, ABSENCES, HOW_TO, SHOWCASE)
        if part not in screen
    ]
    assert missing == [], "the first screen is missing: " + ", ".join(missing)


def test_the_first_screen_says_what_the_problem_is_and_how_a_turn_runs() -> None:
    """The two a reader needs before deciding: what cora is for, and enough of how it
    works to believe it. Both stand above the quick start, so neither is read after the
    decision to install has already been made."""
    screen = sections()

    for part in (PURPOSE, MECHANISM):
        assert part in screen, f"the first screen has no {part}"
        assert len(screen[part].split()) >= 40, (
            f"{part} is a heading with nothing under it"
        )


def test_the_first_screen_says_what_writing_a_plugin_involves() -> None:
    """The contract is the product, so the reader deciding whether cora fits their field
    is the reader this section is for. A link on its own would send them away to find
    out; what it takes has to be answerable here."""
    screen = sections()

    assert EXTENDING in screen, f"the first screen has no {EXTENDING}"
    assert len(screen[EXTENDING].split()) >= 40, (
        "the how-to is linked but not summarised"
    )
    assert HOW_TO in screen[EXTENDING], "the section does not link the how-to"
