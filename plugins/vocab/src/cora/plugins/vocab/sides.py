"""Which column of a list is the German one, once somebody has said.

Not a guess. A screenshot is photographed whichever way round the page was printed, and
the file keeps what was read — so the drill cannot tell Apfel from Apple by looking, and
a rule about the left column is a rule that is silently wrong for half the lists.

Kept in the plugin's own store rather than for the conversation, because a list is
photographed once and drilled for months: asked once, and never again for that list.
"""

import json

LEFT = "left"
RIGHT = "right"


def sides_in(written: str | None) -> dict[str, str]:
    """Which side is German, per list, or nothing where nobody has said.

    Unreadable text reads as nothing said: what is lost is an answer the model can give
    again, and refusing would strand every list behind a file nobody can see.
    """
    try:
        read = json.loads(written or "{}")
        return {
            str(name): str(side) for name, side in read.items() if side in (LEFT, RIGHT)
        }
    except (ValueError, AttributeError, TypeError):
        return {}


def written(sides: dict[str, str]) -> str:
    """These, as the text to keep."""
    return json.dumps(sides, sort_keys=True)


def other(side: str) -> str:
    """The side that is not this one."""
    return RIGHT if side == LEFT else LEFT
