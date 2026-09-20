"""The pairs a field's lists hold, read out of whatever shape the list is in.

Read rather than kept, because the lists are the reader's: one edited between sessions
is edited for the next word put to them, and a word taken out of a list is a word the
drill stops asking.

Two shapes, because the reader has two ways of making a list. A Markdown table is what
somebody writes by hand, and its header names the two sides. A line per pair is what the
reading of a screenshot saves — numbered, em-dashed, and carrying whatever the
recognition got slightly wrong — and it names nothing, so the sides are unnamed and the
drill says "the other side" rather than a language.
"""

import re
from dataclasses import dataclass

_HEADER = re.compile(r"^\|(?P<left>[^|\n]+)\|(?P<right>[^|\n]+)\|\s*$", re.MULTILINE)
_ROW = re.compile(r"^\|(?P<left>[^|\n]*)\|(?P<right>[^|\n]*)\|\s*$", re.MULTILINE)
# A number, a bullet or a letter the recognition put in front of the pair.
_LEADER = re.compile(r"^\s*(?:\d+\s*[.,)]|[-*•])\s*")
# What separates two words: a dash of the kind no word holds, a spaced hyphen, a tab,
# or a gap wide enough to have been a column.
_GAP = re.compile("\\s*[\u2014\u2013]\\s*|\\s+-\\s+|\\t+|\\s{2,}")
_RULE = re.compile(r"^[\s:|-]+$")


@dataclass(frozen=True)
class Pair:
    """One word and its other side, and where they were read from.

    `sides` is what the list calls its two columns where it says — a table's header —
    and two empty strings where it does not. It is the drill's to repeat, not to
    interpret: which of them is the language being learnt is the reader's to know.
    """

    left: str
    right: str
    sides: tuple[str, str]
    source: str


def pairs_in(text: str, source: str) -> tuple[Pair, ...]:
    """Every pair this list holds, in the order it holds them."""
    table = _table(text, source)
    return table if table else _lines(text, source)


def _table(text: str, source: str) -> tuple[Pair, ...]:
    rows = [
        (row.group("left").strip(), row.group("right").strip())
        for row in _ROW.finditer(text)
    ]
    named = [(left, right) for left, right in rows if not _RULE.fullmatch(left + right)]
    if len(named) < 2:
        return ()
    sides, *pairs = named
    return tuple(
        Pair(left=left, right=right, sides=sides, source=source)
        for left, right in pairs
        if left and right
    )


def _lines(text: str, source: str) -> tuple[Pair, ...]:
    found = []
    for line in text.splitlines():
        said = _LEADER.sub("", line).strip()
        if not said or said.startswith("#"):
            continue
        halves = _GAP.split(said, maxsplit=1)
        if len(halves) != 2:
            continue
        left, right = (half.strip() for half in halves)
        if left and right:
            found.append(Pair(left=left, right=right, sides=("", ""), source=source))
    return tuple(found)
