"""Which column of a list is the German one, once somebody has said.

Not a guess. A screenshot is photographed whichever way round the page was printed, and
the file keeps what was read — so the drill cannot tell Apfel from Apple by looking, and
a rule about the left column is a rule that is silently wrong for half the lists.

Kept in the plugin's own store rather than for the conversation, because a list is
photographed once and drilled for months: asked once, and never again for that list.
"""

from cora.plugins.vocab.kept import as_text, read_object

LEFT = "left"
RIGHT = "right"


def sides_in(written: str | None) -> dict[str, str]:
    """Which side is German, per list, or nothing where nobody has said.

    A side that is neither is left out: what is kept here answers a question with two
    answers, and a third is not one of them.
    """
    read = read_object(written)
    return {
        str(name): str(side) for name, side in read.items() if side in (LEFT, RIGHT)
    }


def written(sides: dict[str, str]) -> str:
    """These, as the text to keep."""
    return as_text(dict(sides))


def other(side: str) -> str:
    """The side that is not this one."""
    return RIGHT if side == LEFT else LEFT
