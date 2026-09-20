"""The pairs a field's lists hold, read out of the Markdown each time they are wanted.

Read rather than kept, because the lists are the reader's: one edited between sessions
is edited for the next word put to them, and a word taken out of a list is a word the
drill stops asking.
"""

import re
from dataclasses import dataclass

_HEADING = re.compile(r"^#\s+(?P<language>[^—\n]+?)(?:\s+—.*)?$", re.MULTILINE)
_ROW = re.compile(r"^\|(?P<german>[^|\n]*)\|(?P<learning>[^|\n]*)\|\s*$", re.MULTILINE)
_RULE = re.compile(r"^[\s:-]+$")
_HEADER = ("deutsch", "german")


@dataclass(frozen=True)
class Pair:
    """One word in two languages, and which language the second one is."""

    german: str
    learning: str
    language: str


def pairs_in(text: str) -> tuple[Pair, ...]:
    """Every pair this list holds, in the order it holds them."""
    heading = _HEADING.search(text)
    language = heading.group("language").strip() if heading else ""
    found = []
    for row in _ROW.finditer(text):
        german = row.group("german").strip()
        learning = row.group("learning").strip()
        if not german or not learning:
            continue
        if _RULE.fullmatch(german) or german.lower() in _HEADER:
            continue
        found.append(Pair(german=german, learning=learning, language=language))
    return tuple(found)
