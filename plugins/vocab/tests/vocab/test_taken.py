"""A right answer is the drill's to take: the next word, and no model asked.

Driven through the real taking step, because that is where the field's state is bound
and where the question arrives — a test calling the handler by hand would pass over a
version that only worked inside a tool call.
"""

from collections.abc import Iterator
from contextlib import contextmanager

from cora.engine import keeping
from cora.engine.plugin_set import Registry
from cora.engine.scoping import running_in
from cora.engine.steps import TakeStep
from cora.plugins.vocab import SCOPE, extend
from cora.ports.chat_model import Message
from cora.ports.host import TOOL
from fakes import FakeFiles, FakeStore, host_for

MODULE = "cora.plugins.vocab"
LISTED = "unit.md"
PAIRS = {"Apfel": "apple", "Hund": "dog", "Haus": "house", "Baum": "tree"}
UNIT = "| Deutsch | English |\n| --- | --- |\n" + "".join(
    f"| {german} | {english} |\n" for german, english in PAIRS.items()
)
ONE = "| Deutsch | English |\n| --- | --- |\n| Hund | dog |\n"
ENGLISH = {english: german for german, english in PAIRS.items()}


def _other(shown: str) -> str:
    return PAIRS.get(shown) or ENGLISH[shown]


class Field:
    """One vocab field, its tools, the taking step, and what the conversation kept."""

    def __init__(self, held: str = UNIT) -> None:
        host = host_for(
            MODULE, files=FakeFiles({(SCOPE, LISTED): held}), store=FakeStore()
        )
        extend(host)
        self.tools = {
            entry.value.name: entry.value.run
            for entry in host.registered
            if entry.kind == TOOL
        }
        self.drill = self.tools["next_word"].__self__
        self.step = TakeStep(registry=Registry(tuple(host.registered)))
        self.kept: dict[str, dict[str, str]] = {}

    @contextmanager
    def drilling(self) -> Iterator[None]:
        with keeping.bound(self.kept), running_in(frozenset({SCOPE})):
            yield

    def put(self, **asked: object) -> str:
        with self.drilling():
            self.tools["german_side"](name=LISTED, side="left")
            self.tools["next_word"](**asked)
        return self.drill.current.shown

    def answers(self, written: str) -> str | None:
        """What the reader reads back from the drill itself, or nothing where the turn
        went on to the model."""
        contributed = self.step(
            {
                "question": written,
                "messages": [Message(role="user", content=written)],
                "turn_start": 0,
                "scopes": [SCOPE],
                "kept": self.kept,
            }
        )
        self.kept = contributed["kept"]
        taken = contributed.get("messages", [])
        return taken[0].content if taken else None

    def queued(self) -> list[str]:
        return [pair.left for pair in self.drill.current.queue]


def test_the_other_side_answered_gets_the_next_word_and_the_pass_moves_on() -> None:
    field = Field()
    shown = field.put()
    left = len(field.queued())

    put = field.answers(_other(shown))

    assert put is not None and put in PAIRS and put != shown
    assert field.drill.current.shown == put
    assert len(field.queued()) == left - 1
    assert shown not in field.queued(), "a word produced does not come back"


def test_case_and_a_closing_full_stop_do_not_stop_an_answer_being_right() -> None:
    field = Field()
    shown = field.put()

    assert field.answers(_other(shown).capitalize() + ".") is not None


def test_an_answer_that_is_not_the_word_is_left_to_the_model_and_moves_nothing() -> (
    None
):
    field = Field()
    shown = field.put()
    queued = field.queued()

    assert field.answers("banana") is None
    assert field.drill.current.shown == shown
    assert field.queued() == queued


def test_a_hint_asked_for_is_left_to_the_model() -> None:
    field = Field()
    shown = field.put()

    assert field.answers("h") is None
    assert field.drill.current.shown == shown


def test_the_last_word_of_a_pass_is_left_to_the_model_even_answered_right() -> None:
    field = Field(ONE)
    shown = field.put()

    assert field.answers(_other(shown)) is None
    assert field.drill.current.shown == shown, "the word is still on the table"
    assert field.queued() == []


def test_a_spaced_session_is_left_to_the_model() -> None:
    field = Field()
    shown = field.put(spaced=True)

    assert field.answers(_other(shown)) is None
    assert field.drill.current.shown == shown


def test_the_other_way_round_is_judged_against_the_german_side() -> None:
    field = Field()
    shown = field.put(put="other")
    assert shown in ENGLISH

    put = field.answers(ENGLISH[shown])

    assert put is not None and put in ENGLISH


def test_nothing_on_the_table_leaves_every_answer_to_the_model() -> None:
    field = Field()

    assert field.answers("dog") is None


def test_a_right_answer_after_a_hint_counts_as_missed_and_the_word_comes_round() -> (
    None
):
    field = Field()
    shown = field.put()
    assert field.answers("h") is None, "the model was asked, and the word stayed"

    put = field.answers(_other(shown))

    assert put is not None and put != shown
    assert shown in field.queued(), "a word that took a hint comes round again"


def test_a_right_answer_after_the_word_moved_through_the_model_is_right() -> None:
    field = Field()
    shown = field.put()
    assert field.answers("banana") is None
    # The model records the miss and puts the next word, as it does today.
    with field.drilling():
        field.tools["how_it_went"](word=shown, right=False)
        field.tools["next_word"]()
    moved = field.drill.current.shown

    put = field.answers(_other(moved))

    assert put is not None
    assert moved not in field.queued(), "nothing about the word before it lingers"
