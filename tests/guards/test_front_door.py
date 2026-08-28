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
