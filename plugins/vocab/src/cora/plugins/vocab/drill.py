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
FROM_GERMAN = "from_german"
DONE = "Nothing is due and nothing is new — the session is done."
NO_WORDS = "This field holds no word lists yet."
NO_STORE = "This deployment keeps nothing, so a drill here could not remember anything."
UNASKED = "That word was not the one asked. Put a word first, then say how it went."


@dataclass(frozen=True)
class Drill:
    """The field's two tools, closed over the cora holding its lists and its store."""

    cora: Host

    def next_word(self, direction: str = FROM_GERMAN) -> str:
        """The word to put to the reader, from the side they are being asked."""
        pairs = self._pairs()
        if not pairs:
            return NO_WORDS
        schedule = Schedule.of(self._kept().read(SCHEDULE))
        today = datetime.date.today()
        waiting = [
            (place, pair)
            for place, pair in enumerate(pairs)
            if due(schedule.card(pair.learning), today)
        ]
        if not waiting:
            return DONE
        # The longest overdue first, then a word already drilled ahead of one never
        # seen — a lapse is what the session is for, and new words are what it fills up
        # with. The reader's own order under that: a list is written in the order it
        # was learnt in, and alphabetical is nobody's order.
        _, asking = min(waiting, key=lambda each: _turn(schedule, each, today))
        self.cora.state.keep(ASKED, asking.learning)
        put = asking.learning if direction != FROM_GERMAN else asking.german
        return f"{put} — {asking.language} list, ask for the other side."

    def how_it_went(self, word: str, right: bool) -> str:
        """Move the schedule of the word just put, by whether the reader produced it."""
        asked = self.cora.state.read(ASKED)
        pair = self._of(word)
        if asked is None or pair is None or pair.learning != asked:
            raise ToolRefusal(UNASKED)
        kept = self._kept()
        schedule = Schedule.of(kept.read(SCHEDULE))
        card = reviewed(
            schedule.card(pair.learning), right=right, today=datetime.date.today()
        )
        kept.keep(SCHEDULE, schedule.with_card(pair.learning, card).written())
        self.cora.state.keep(ASKED, None)
        return "again in this session" if not right else f"next in {card.interval} days"

    def _pairs(self) -> tuple[Pair, ...]:
        return tuple(
            pair
            for document in self.cora.documents.all()
            for pair in pairs_in(document.text)
        )

    def _of(self, word: str) -> Pair | None:
        said = word.strip().casefold()
        for pair in self._pairs():
            if said in (pair.german.casefold(), pair.learning.casefold()):
                return pair
        return None

    def _kept(self) -> Kept:
        if self.cora.store is None:
            raise ToolRefusal(NO_STORE)
        return self.cora.store


def _turn(
    schedule: Schedule, waiting: tuple[int, Pair], today: datetime.date
) -> tuple[datetime.date, int, int]:
    place, pair = waiting
    card = schedule.card(pair.learning)
    return (card.due or today, 1 if card.due is None else 0, place)
