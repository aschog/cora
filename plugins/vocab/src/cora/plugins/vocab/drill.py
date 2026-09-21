"""Putting a word and taking the answer: the two calls the drill runs on.

The model does the talking — which way round, the hint, whether what the reader typed
counts. What it does not do is decide when a word comes back: that is the schedule's,
and the schedule is arithmetic.
"""

import datetime
import random
from dataclasses import dataclass

from cora.ports.host import Host
from cora.ports.plugin import ToolRefusal
from cora.ports.store import Kept

from .schedule import Schedule
from .sm2 import due, reviewed
from .sweep import Sweep
from .words import Pair, pairs_of

SCHEDULE = "schedule"
ASKED = "asked"
CHOSEN = "chosen"
SIDE = "side"
SPACED = "spaced"
SWEPT = "swept"
ON = "1"
LEFT = "left"
# No file can be called this — a name is one plain name — so no list can ever be
# confused with the choice to drill all of them.
EVERY = "*"
DONE = "Nothing is due and nothing is new — the session is done."
SWEPT_UP = (
    "Every word on this list has been produced — the pass is done. Ask the reader "
    "whether to go again, and call this with `again` where they say yes."
)
AGAIN = "again in this pass"
NO_WORDS = "This field holds no word lists yet."
NO_STORE = "This deployment keeps nothing, so a drill here could not remember anything."
UNASKED = "That word was not the one asked. Put a word first, then say how it went."
UNCHOSEN = (
    "This field holds more than one list, so ask the reader which one to drill before "
    "putting a word: {held}, or all of them. Put it on a card with ask_user, then call "
    "this again with `from_list` set to what they chose, or '*' for all of them."
)
NO_SUCH_LIST = "This field holds no list called '{name}'. It holds: {held}."


@dataclass(frozen=True)
class Drill:
    """The field's two tools, closed over the cora holding its lists and its store."""

    cora: Host

    def next_word(
        self,
        side: str = "",
        from_list: str = "",
        spaced: bool | None = None,
        again: bool = False,
    ) -> str:
        """The word to put to the reader, from the side they are being asked."""
        pairs = pairs_of(self.cora)
        if not pairs:
            return NO_WORDS
        pairs = self._chosen(pairs, from_list)
        if again:
            self.cora.state.keep(SWEPT, None)
        asking = self._due(pairs) if self._spacing(spaced) else self._still_to_do(pairs)
        if asking is None:
            return DONE if self._spacing(None) else SWEPT_UP
        self.cora.state.keep(ASKED, _key(asking))
        asking_left = self._side(side) == LEFT
        put = asking.left if asking_left else asking.right
        return f"{put} — from {asking.source}{_sides(asking, asking_left)}."

    def how_it_went(self, word: str, right: bool) -> str:
        """Move the word just put, by whether the reader produced it.

        Where spacing is on that is the schedule, and where it is off it is this pass —
        so a session nobody asked to space writes nothing that outlives it.
        """
        asked = self.cora.state.read(ASKED)
        if asked is None or word.strip().casefold() not in _both(asked):
            raise ToolRefusal(UNASKED)
        self.cora.state.keep(ASKED, None)
        if not self._spacing(None):
            return self._swept(asked, right=right)
        kept = self._kept()
        schedule = Schedule.of(kept.read(SCHEDULE))
        card = reviewed(schedule.card(asked), right=right, today=datetime.date.today())
        kept.keep(SCHEDULE, schedule.with_card(asked, card).written())
        return "again in this session" if not right else f"next in {card.interval} days"

    def _swept(self, asked: str, *, right: bool) -> str:
        if not right:
            return AGAIN
        sweep = Sweep.of(self.cora.state.read(SWEPT))
        self.cora.state.keep(SWEPT, sweep.with_word(asked).written())
        return "done for this pass"

    def _due(self, pairs: tuple[Pair, ...]) -> Pair | None:
        schedule = Schedule.of(self._kept().read(SCHEDULE))
        today = datetime.date.today()
        waiting = [
            (place, pair)
            for place, pair in enumerate(pairs)
            if due(schedule.card(_key(pair)), today)
        ]
        if not waiting:
            return None
        # The longest overdue first, then a word already drilled ahead of one never
        # seen — a lapse is what the session is for, and new words are what it fills up
        # with. The reader's own order under that: a list is written in the order it
        # was learnt in, and alphabetical is nobody's order.
        _, asking = min(waiting, key=lambda each: _turn(schedule, each, today))
        return asking

    def _still_to_do(self, pairs: tuple[Pair, ...]) -> Pair | None:
        # A shuffle without a stored order: one taken at random from what the pass has
        # not got yet is the same thing, and there is no order to keep in step with a
        # list the reader can edit while the session runs.
        sweep = Sweep.of(self.cora.state.read(SWEPT))
        left = [pair for pair in pairs if not sweep.holds(_key(pair))]
        return random.choice(left) if left else None

    def _spacing(self, asked: bool | None) -> bool:
        if asked is not None:
            self.cora.state.keep(SPACED, ON if asked else None)
            return asked
        return self.cora.state.read(SPACED) == ON

    def _side(self, asked: str) -> str:
        # German is the left column of a list, so the left side is what a drill puts
        # until the reader turns it round.
        if asked.strip():
            self.cora.state.keep(SIDE, asked.strip())
            return asked.strip()
        return self.cora.state.read(SIDE) or LEFT

    def _chosen(self, pairs: tuple[Pair, ...], asked: str) -> tuple[Pair, ...]:
        # Settled three ways: named in this call, chosen earlier in the conversation,
        # or the only list there is. A refusal names the lists, because the reader is
        # about to be offered them.
        held = _sources(pairs)
        chosen = asked.strip() or self.cora.state.read(CHOSEN) or ""
        if not chosen:
            if len(held) > 1:
                raise ToolRefusal(UNCHOSEN.format(held=", ".join(held)))
            chosen = EVERY
        if chosen != EVERY and chosen not in held:
            raise ToolRefusal(NO_SUCH_LIST.format(name=chosen, held=", ".join(held)))
        self.cora.state.keep(CHOSEN, chosen)
        if chosen == EVERY:
            return pairs
        return tuple(pair for pair in pairs if pair.source == chosen)

    def _kept(self) -> Kept:
        if self.cora.store is None:
            raise ToolRefusal(NO_STORE)
        return self.cora.store


# A word's name in the schedule is the pair itself: a list edited drops what it dropped,
# and one side alone would collide with the same word on another list.
def _key(pair: Pair) -> str:
    return f"{pair.left}|{pair.right}"


def _sources(pairs: tuple[Pair, ...]) -> list[str]:
    return list(dict.fromkeys(pair.source for pair in pairs))


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
