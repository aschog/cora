"""One sentence about what cora is, said in four places, kept in step.

`README.md` is where the project describes itself — the repository's front door, and the
long description of the distribution. The other three cannot simply link to it: the docs
site's front page needs the paragraph on the page rather than a pointer to another one,
packaging metadata cannot read a file at all, and `CLAUDE.md` is read by an agent that
should not follow a link to learn what it is working on. So there are copies, and this
is what stops one of them drifting into a description of an older project.
"""

import workspace

README = workspace.ROOT / "README.md"
FRONT_PAGE = workspace.ROOT / "docs" / "index.md"
BRIEFING = workspace.ROOT / "CLAUDE.md"


def _flat(text: str) -> str:
    """The text with its line wrapping taken out, so a rewrap is not a difference."""
    return " ".join(text.split())


def tagline() -> str:
    """The paragraph `README.md` opens with, under its title."""
    _, paragraph, *_ = README.read_text().split("\n\n", 2)
    return _flat(paragraph)


def opening() -> str:
    """Its first sentence — as much as a one-line description has room for."""
    return tagline().split(". ")[0]


def test_the_docs_front_page_opens_with_the_readmes_own_words() -> None:
    assert tagline() in _flat(FRONT_PAGE.read_text()), (
        "docs/index.md describes cora differently from README.md"
    )


def test_the_distribution_is_described_by_the_same_sentence() -> None:
    """`description` is what an index shows beside the name, so it leads with the same
    sentence and then says what this distribution in particular holds."""
    described = workspace.manifest(workspace.ROOT)["project"]["description"]

    assert described.startswith(opening()), (
        "pyproject.toml's description does not open the way README.md does"
    )


def test_the_briefing_says_the_same_thing() -> None:
    assert opening() in _flat(BRIEFING.read_text()), (
        "CLAUDE.md would tell the next session it is working on something else"
    )
