"""Every word's standing, as one piece of text the plugin keeps.

JSON under one name rather than a row per word: picking a word reads the whole thing
anyway, and a list somebody is learning from is tens of words rather than thousands.
Unreadable text reads as an empty schedule — a plugin that refused to start over what
it had written itself would need a file the reader cannot see to be deleted by hand.
"""

import datetime
from dataclasses import dataclass, field
from typing import Any

from cora.plugins.vocab.kept import as_text, read_object
from cora.plugins.vocab.sm2 import Card

DUE = "due"
INTERVAL = "interval"
EASE = "ease"
RIGHT = "right"


@dataclass(frozen=True)
class Schedule:
    """What every word that has been drilled is waiting on, keyed by the word itself."""

    cards: dict[str, Card] = field(default_factory=dict)

    @classmethod
    def of(cls, written: str | None) -> "Schedule":
        """The schedule this text holds, or an empty one where it holds none."""
        read = read_object(written)
        return cls({word: _card(each) for word, each in read.items()})

    def written(self) -> str:
        """This schedule as the text to keep."""
        return as_text({word: _written(card) for word, card in self.cards.items()})

    def card(self, word: str) -> Card:
        """Where this word stands, or a fresh card for one never drilled."""
        return self.cards.get(word, Card())

    def with_card(self, word: str, card: Card) -> "Schedule":
        """This schedule with one word's standing replaced, and no other touched."""
        return Schedule({**self.cards, word: card})


def _card(written: Any) -> Card:
    due = written.get(DUE)
    return Card(
        due=datetime.date.fromisoformat(due) if due else None,
        interval=int(written.get(INTERVAL, 0)),
        ease=float(written.get(EASE, Card().ease)),
        right=int(written.get(RIGHT, 0)),
    )


def _written(card: Card) -> dict[str, Any]:
    return {
        DUE: card.due.isoformat() if card.due else None,
        INTERVAL: card.interval,
        EASE: card.ease,
        RIGHT: card.right,
    }
