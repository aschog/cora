"""SuperMemo-2, as arithmetic on one word.

Wozniak's published algorithm, which is what every flashcard program still spaces by: an
interval in days and an ease that grows on the words that prove easy. A word answered
right waits a day, then six, then its last interval widened by its ease. A word missed
starts again, and is due the moment it was missed — the reader is still sitting there.
"""

import datetime
from dataclasses import dataclass

FIRST = 1
SECOND = 6
EASE = 2.5
EASE_FLOOR = 1.3
EASE_LOST = 0.2
EASE_GAINED = 0.1


@dataclass(frozen=True)
class Card:
    """One word's standing: when it is next due, how far apart its repeats are, and how
    easy it has proved. A card nobody has answered is due now, which is what makes a
    word never drilled a word to drill."""

    due: datetime.date | None = None
    interval: int = 0
    ease: float = EASE
    right: int = 0


def due(card: Card, today: datetime.date) -> bool:
    """Whether this word is one to put to the reader now."""
    return card.due is None or card.due <= today


def reviewed(card: Card, *, right: bool, today: datetime.date) -> Card:
    """The card this one becomes once the reader has answered it.

    Args:
        right: Whether they produced the word. A hint counts as a miss, which is the
            drill's business rather than this one's.
        today: The day the answer was given, which every date is measured from.
    """
    if not right:
        return Card(
            due=today,
            interval=0,
            ease=max(EASE_FLOOR, card.ease - EASE_LOST),
            right=0,
        )
    ease = card.ease + EASE_GAINED
    if card.right == 0:
        interval = FIRST
    elif card.right == 1:
        interval = SECOND
    else:
        interval = round(card.interval * card.ease)
    return Card(
        due=today + datetime.timedelta(days=interval),
        interval=interval,
        ease=ease,
        right=card.right + 1,
    )
