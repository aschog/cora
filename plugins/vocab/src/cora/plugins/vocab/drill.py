"""Putting a word and taking the answer: the two calls the drill runs on.

The model does the talking — which way round, the hint, whether what the reader typed
counts. What it does not do is decide when a word comes back: that is the schedule's,
and the schedule is arithmetic.
"""

import datetime
from dataclasses import dataclass

from cora.ports.host import Host
from cora.ports.plugin import ToolRefusal
from cora.ports.store import Kept

from .schedule import Schedule
from .sm2 import due, reviewed
from .words import Pair, pairs_in

SCHEDULE = "schedule"
ASKED = "asked"
LEFT = "left"
DONE = "Nothing is due and nothing is new — the session is done."
NO_WORDS = "This field holds no word lists yet."
NO_STORE = "This deployment keeps nothing, so a drill here could not remember anything."
UNASKED = "That word was not the one asked. Put a word first, then say how it went."


@dataclass(frozen=True)
class Drill:
    """The field's two tools, closed over the cora holding its lists and its store."""

    cora: Host
    scope: str

    def next_word(self, side: str = LEFT) -> str:
        """The word to put to the reader, from the side they are being asked."""
        pairs = self._pairs()
        if not pairs:
            return NO_WORDS
        schedule = Schedule.of(self._kept().read(SCHEDULE))
        today = datetime.date.today()
        waiting = [
            (place, pair)
            for place, pair in enumerate(pairs)
            if due(schedule.card(_key(pair)), today)
        ]
        if not waiting:
            return DONE
        # The longest overdue first, then a word already drilled ahead of one never
        # seen — a lapse is what the session is for, and new words are what it fills up
        # with. The reader's own order under that: a list is written in the order it
        # was learnt in, and alphabetical is nobody's order.
        _, asking = min(waiting, key=lambda each: _turn(schedule, each, today))
        self.cora.state.keep(ASKED, _key(asking))
        asking_left = side == LEFT
        put = asking.left if asking_left else asking.right
        return f"{put} — from {asking.source}{_sides(asking, asking_left)}."

    def how_it_went(self, word: str, right: bool) -> str:
        """Move the schedule of the word just put, by whether the reader produced it."""
        asked = self.cora.state.read(ASKED)
        if asked is None or word.strip().casefold() not in _both(asked):
            raise ToolRefusal(UNASKED)
        kept = self._kept()
        schedule = Schedule.of(kept.read(SCHEDULE))
        card = reviewed(schedule.card(asked), right=right, today=datetime.date.today())
        kept.keep(SCHEDULE, schedule.with_card(asked, card).written())
        self.cora.state.keep(ASKED, None)
        return "again in this session" if not right else f"next in {card.interval} days"

    def _pairs(self) -> tuple[Pair, ...]:
        # A turn can run over more than one field, and what it is handed is every
        # document of every field it is running in. Only this one's are vocabulary.
        return tuple(
            pair
            for document in self.cora.documents.all()
            if document.scope == self.scope
            for pair in pairs_in(document.text, document.name)
        )

    def _kept(self) -> Kept:
        if self.cora.store is None:
            raise ToolRefusal(NO_STORE)
        return self.cora.store


# A word's name in the schedule is the pair itself: a list edited drops what it dropped,
# and one side alone would collide with the same word on another list.
def _key(pair: Pair) -> str:
    return f"{pair.left}|{pair.right}"


def _both(key: str) -> tuple[str, ...]:
    return tuple(side.strip().casefold() for side in key.split("|", 1))


def _sides(pair: Pair, asking_left: bool) -> str:
    wanted = pair.sides[1] if asking_left else pair.sides[0]
    return f", {wanted}" if wanted else ""


def _turn(
    schedule: Schedule, waiting: tuple[int, Pair], today: datetime.date
) -> tuple[datetime.date, int, int]:
    place, pair = waiting
    card = schedule.card(_key(pair))
    return (card.due or today, 1 if card.due is None else 0, place)
