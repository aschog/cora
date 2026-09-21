"""Putting a word and taking the answer: the two calls the drill runs on.

The model does the talking — which way round, the hint, whether what the reader typed
counts. What it does not do is decide when a word comes back: that is the schedule's,
and the schedule is arithmetic.
"""

import datetime
import random
import re
from dataclasses import dataclass, field

from cora.ports.host import Host
from cora.ports.plugin import ToolRefusal
from cora.ports.store import Kept

from .schedule import Schedule
from .sides import LEFT as GERMAN_LEFT
from .sides import other, sides_in
from .sides import written as sides_written
from .sm2 import due, reviewed
from .words import Pair, pairs_of

SCHEDULE = "schedule"
SIDES = "sides"
CHOSEN = "chosen"
PUT = "put"
GERMAN = "german"
OTHER = "other"
SPACED = "spaced"
ON = "1"
# No file can be called this — a name is one plain name — so no list can ever be
# confused with the choice to drill all of them.
EVERY = "*"
DONE = "Nothing is due and nothing is new — the session is done."
# What a tool hands back is read by the model and half-repeated to the reader, so it
# says what happened and never what to call next: an instruction here comes out of the
# answer as machinery.
SWEPT_UP = "Every word on this list has been produced — the pass is done."
# What is said back after an answer counts the words left, because "done for this
# pass" was read as the pass being done and ended a session nine words early. A count
# cannot be read as anything but a count.
RIGHT = "right — {left} words still to put in this pass."
MISSED = "missed — it comes round again. {left} words still to put in this pass."
LAST = "right — that was the last word. The pass is done."
NO_WORDS = "This field holds no word lists yet."
NO_STORE = "This deployment keeps nothing, so a drill here could not remember anything."
UNASKED = (
    "'{said}' was not the word asked. The word on the table is '{shown}' — say how "
    "that one went. Do not ask for another word: this one is still unanswered."
)
NOTHING_ASKED = "No word is on the table. Ask for one before saying how it went."
UNSIDED = (
    "Nobody has said which column of {named} is the German one, and a drill puts the "
    "German. Its first pairs are: {pairs}. Work out which side that is and call "
    "german_side, then ask for a word again."
)
UNCHOSEN = (
    "This field holds more than one list, so ask the reader which one to drill before "
    "putting a word: {held}, or all of them. Put it on a card with ask_user, then call "
    "this again with `from_list` set to what they chose, or '*' for all of them."
)
NO_SUCH_LIST = "This field holds no list called '{name}'. It holds: {held}."
# What the reader is told, in the field's own language, where the model wrote a word
# that came from nowhere and the drill could not put a real one in its place.
MARKUP = re.compile(r"[*_`~]+")
CLOSING = re.compile(r"[.!?…:;,]+\Z")
# Enough of a list for the model to tell one language from the other, and few enough
# that a refusal is a sentence rather than the list itself.
SAMPLED = 4


@dataclass
class Pass:
    """One shuffled pass over one list, and the word on the table right now.

    Held in memory for the life of the process, not in the conversation's state.
    # ponytail: one drill per process; per-conversation state if two ever run.
    A second conversation drilling at the same time would draw from this same queue,
    and a restart drops a pass part-way. For one reader at one screen, neither bites,
    and what it buys is a queue that is a list — popped, appended to, emptied.
    """

    of: str = ""
    queue: list[Pair] = field(default_factory=list)
    table: Pair | None = None
    shown: str = ""
    loaded: bool = False

    def reload(self, pairs: tuple[Pair, ...], of: str) -> None:
        """A fresh pass over these pairs, in a fresh order."""
        self.of = of
        self.queue = list(pairs)
        random.shuffle(self.queue)
        self.loaded = True
        self.table = None
        self.shown = ""


@dataclass(frozen=True)
class Drill:
    """The field's two tools, closed over the cora holding its lists and its store."""

    cora: Host
    current: Pass = field(default_factory=Pass)

    def next_word(
        self,
        put: str = "",
        from_list: str = "",
        spaced: bool | None = None,
        again: bool = False,
    ) -> str:
        """The word to put to the reader, from the side they are being asked."""
        pairs = pairs_of(self.cora)
        if not pairs:
            return NO_WORDS
        # A conversation that has chosen nothing yet is a new one, and a new one starts
        # a fresh pass — the queue outlives the conversation, so this is what ends it.
        fresh = self.cora.state.read(CHOSEN) is None
        pairs = self._chosen(pairs, from_list)
        self._refuse_unsided(pairs)
        chosen = self.cora.state.read(CHOSEN) or EVERY
        if again or fresh or not self.current.loaded or self.current.of != chosen:
            self.current.reload(pairs, chosen)
        if self._spacing(spaced):
            asking = self._due(pairs)
        elif self.current.table is not None:
            # A word already put and not yet answered is still the word being asked.
            # Asking twice is what a model does when a call of its own was refused, and
            # a pass that popped each time would lose a word to every refusal.
            asking = self.current.table
        else:
            asking = self.current.queue.pop(0) if self.current.queue else None
        if asking is None:
            return DONE if self._spacing(None) else SWEPT_UP
        word, left = self._shown(asking, put, pairs)
        return f"{word} — from {asking.source}{_sides(asking, left)}."

    def taken(self, answer: str) -> str | None:
        """The next word, where the answer is the other side of the word on the table.

        Letter for letter, case aside: anything looser is a judgement, and judging is
        the model's — so a hint, a miss and everything else here go on to the model.
        """
        asking, shown = self.current.table, self.current.shown
        if asking is None or not shown:
            return None
        if _plain(answer) != _other_side(asking, shown).casefold():
            return None
        self.how_it_went(word=shown, right=True)
        self.next_word()
        return self.current.shown

    def checked(self, answer: str) -> str | None:
        """The answer, unless it is a word off no list — then the one on the table.

        A model will go on writing the column of single words without asking for the
        next one: `Apfel`, then `Apfelbaum`, from nowhere. The word on the table is put
        again, because nothing answered it and it is still the word being asked.

        Three things hold before this changes anything: a word is on the table and
        unanswered, the answer is one bare word, and that word is on no list here.
        """
        # Outside a tool call, where a plugin's own state is not bound — so it reads
        # the pass in memory and the field's lists, and keeps nothing.
        asking, shown = self.current.table, self.current.shown
        if asking is None or not shown:
            return None
        word = _bare(answer)
        if word is None or word.casefold() == shown.casefold():
            return None
        if word.casefold() in _spoken(pairs_of(self.cora)):
            return None
        return shown

    def _shown(
        self, asking: Pair, put: str, pairs: tuple[Pair, ...]
    ) -> tuple[str, bool]:
        german = self._german(asking.source, pairs)
        showing = german if self._putting(put) == GERMAN else other(german)
        left = showing == GERMAN_LEFT
        word = asking.left if left else asking.right
        self.current.table = asking
        self.current.shown = word
        return word, left

    def how_it_went(self, word: str, right: bool) -> str:
        """Move the word just put, by whether the reader produced it.

        Where spacing is on that is the schedule, and where it is off it is this pass —
        so a session nobody asked to space writes nothing that outlives it.
        """
        asking = self.current.table
        if asking is None:
            raise ToolRefusal(NOTHING_ASKED)
        if word.strip().casefold() not in _both(_key(asking)):
            raise ToolRefusal(
                UNASKED.format(said=word.strip(), shown=self.current.shown)
            )
        self.current.table = None
        self.current.shown = ""
        if not self._spacing(None):
            # A word missed goes to the back of the queue and comes round again; a word
            # produced is simply gone from it.
            if not right:
                self.current.queue.append(asking)
            left = len(self.current.queue)
            if not left:
                return LAST
            return (RIGHT if right else MISSED).format(left=left)
        kept = self._kept()
        schedule = Schedule.of(kept.read(SCHEDULE))
        key = _key(asking)
        card = reviewed(schedule.card(key), right=right, today=datetime.date.today())
        kept.keep(SCHEDULE, schedule.with_card(key, card).written())
        return "again in this session" if not right else f"next in {card.interval} days"

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

    def _spacing(self, asked: bool | None) -> bool:
        if asked is not None:
            self.cora.state.keep(SPACED, ON if asked else None)
            return asked
        return self.cora.state.read(SPACED) == ON

    def _refuse_unsided(self, pairs: tuple[Pair, ...]) -> None:
        # One list at a time: the model has to look at each one's words to say which
        # column they are, and a refusal carrying five lists carries none of them well.
        for named in _sources(pairs):
            if self._german(named, pairs):
                continue
            sample = [pair for pair in pairs if pair.source == named][:SAMPLED]
            raise ToolRefusal(
                UNSIDED.format(
                    named=named,
                    pairs="; ".join(f"{one.left} — {one.right}" for one in sample),
                )
            )

    def _putting(self, asked: str) -> str:
        # The German side unless the reader turns it round, and then for the rest of
        # the conversation.
        if asked.strip():
            self.cora.state.keep(PUT, asked.strip())
            return asked.strip()
        return self.cora.state.read(PUT) or GERMAN

    def _german(self, named: str, pairs: tuple[Pair, ...]) -> str:
        # Which column is German is the model's to say, once per list — a screenshot is
        # photographed whichever way round the page was, and nothing here can tell
        # Apfel from Apple. Where a deployment keeps nothing there is nowhere to put
        # the answer, so the left column stands in.
        if self.cora.store is None:
            return GERMAN_LEFT
        return sides_in(self.cora.store.read(SIDES)).get(_sided(named, pairs), "")

    def german_side(self, name: str, side: str) -> str:
        """Say which column of a list holds the German, for good."""
        pairs = pairs_of(self.cora)
        held = _sources(pairs)
        if name not in held:
            raise ToolRefusal(NO_SUCH_LIST.format(name=name, held=", ".join(held)))
        kept = self._kept()
        sides = sides_in(kept.read(SIDES))
        kept.keep(SIDES, sides_written({**sides, _sided(name, pairs): side}))
        return f"{side} is the German column of {name}."

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


def _plain(answer: str) -> str:
    return answer.strip().casefold()


def _other_side(pair: Pair, shown: str) -> str:
    return pair.right if shown == pair.left else pair.left


def _bare(answer: str) -> str | None:
    # One word, stripped of the markup a model wraps it in; anything with a space in it
    # is a sentence, or a phrase from the list, and not this check's business.
    word = CLOSING.sub("", MARKUP.sub("", answer).strip())
    return word if word and not re.search(r"\s", word) else None


# The store is one plugin's, not one field's, so a list is named there by more than its
# filename: two fields that both hold `einheit-3.md` are two lists, and each answers for
# its own column. The first pair is what tells them apart, and it survives a second
# photograph being appended to either.
def _sided(named: str, pairs: tuple[Pair, ...]) -> str:
    for pair in pairs:
        if pair.source == named:
            return f"{named}#{pair.left}|{pair.right}"
    return named


def _spoken(pairs: tuple[Pair, ...]) -> frozenset[str]:
    # Every word of every list, either side: what the reader may legitimately say back.
    return frozenset(
        side.casefold() for pair in pairs for side in (pair.left, pair.right)
    )


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
