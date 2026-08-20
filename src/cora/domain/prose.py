"""Sentence fragments cora builds by hand, so a count reads as English."""

from collections.abc import Sequence


def listed(items: Sequence[str]) -> str:
    """The items as a phrase: `a`, `a and b`, `a, b and c`."""
    if len(items) < 2:
        return "".join(items)
    return f"{', '.join(items[:-1])} and {items[-1]}"


def counted(count: int, noun: str) -> str:
    """The count with its noun, pluralised by adding an `s`.

    English enough for the nouns cora counts, which are its own.
    """
    return f"{count} {noun}" if count == 1 else f"{count} {noun}s"
