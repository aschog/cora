"""A session with nothing turned on: one shuffled pass over the list the reader chose.

The default path, which every other drill test turns off by passing `spaced=True`.
What it has to get right is that a pass ends, that a word missed does not, and that a
store nobody asked to fill stays empty.
"""

from collections.abc import Iterator
from contextlib import contextmanager

from pytest import raises

from cora.engine import keeping
from cora.engine.scoping import running_in
from cora.plugins.vocab import SCOPE, extend
from cora.plugins.vocab.drill import SCHEDULE
from cora.ports.host import TOOL
from cora.ports.plugin import ToolRefusal
from fakes import FakeFiles, FakeStore, host_for

MODULE = "cora.plugins.vocab"
LISTED = "unit.md"
WORDS = 8
UNIT = "| Deutsch | English |\n| --- | --- |\n" + "".join(
    f"| D{n} | e{n} |\n" for n in range(WORDS)
)
OTHER = "| Deutsch | English |\n| --- | --- |\n| Hund | dog |\n"
PAIR = "| Deutsch | English |\n| --- | --- |\n| Hund | dog |\n| Haus | house |\n"
ENGLISH, GERMAN = ("dog", "house"), ("Hund", "Haus")


class Field:
    def __init__(self, **held: str) -> None:
        self.store = FakeStore()
        files = {(SCOPE, name): text for name, text in (held or {LISTED: UNIT}).items()}
        host = host_for(MODULE, files=FakeFiles(files), store=self.store)
        extend(host)
        self.tools = {
            entry.value.name: entry.value.run
            for entry in host.registered
            if entry.kind == TOOL
        }

    @contextmanager
    def drilling(self) -> Iterator[None]:
        with keeping.bound({}), running_in(frozenset({SCOPE})):
            yield

    def sided(self, *named: str) -> "Field":
        with self.drilling():
            for name in named or (LISTED,):
                self.tools["german_side"](name=name, side="left")
        return self

    def pass_over(self, missing: str = "", **asked: object) -> tuple[list[str], str]:
        """Answer every word right — bar one, missed the first time it is put."""
        put: list[str] = []
        for _ in range(WORDS * 3):
            said = self.tools["next_word"](**asked)
            if " — from " not in said:
                return put, said
            word = said.split(" — ")[0]
            put.append(word)
            right = word != missing or put.count(missing) > 1
            self.tools["how_it_went"](word=word, right=right)
            asked = {}
        raise AssertionError("the pass never ended")


def test_every_word_is_put_once_and_the_pass_ends() -> None:
    field = Field().sided()

    with field.drilling():
        put, ended = field.pass_over()

    assert sorted(put) == sorted(f"D{n}" for n in range(WORDS))
    assert "pass is done" in ended


def test_a_word_missed_comes_back_before_the_pass_ends() -> None:
    field = Field().sided()

    with field.drilling():
        put, ended = field.pass_over(missing="D3")

    assert put.count("D3") == 2
    assert len(put) == WORDS + 1
    assert "pass is done" in ended


def test_the_count_left_falls_by_one_a_word_and_not_on_a_miss() -> None:
    field = Field().sided()

    with field.drilling():
        first = field.tools["next_word"]().split(" — ")[0]
        right = field.tools["how_it_went"](word=first, right=True)
        second = field.tools["next_word"]().split(" — ")[0]
        missed = field.tools["how_it_went"](word=second, right=False)

    assert f"{WORDS - 1} words still to put" in right
    assert f"{WORDS - 1} words still to put" in missed
    assert "comes round again" in missed


# Shuffled, so a word is learnt rather than its place in the list. Two passes over one
# list agreeing exactly is a 1-in-40320 coincidence, and over three tries impossible
# enough to assert on.
def test_the_order_is_not_the_order_of_the_list() -> None:
    orders = []
    for _ in range(3):
        field = Field().sided()
        with field.drilling():
            put, _ = field.pass_over()
        orders.append(put)

    listed = [f"D{n}" for n in range(WORDS)]
    assert any(order != listed for order in orders)
    assert len({tuple(order) for order in orders}) > 1


def test_a_finished_pass_says_so_rather_than_putting_a_word() -> None:
    field = Field().sided()

    with field.drilling():
        field.pass_over()
        said = field.tools["next_word"]()

    assert "pass is done" in said


def test_going_again_puts_the_words_again() -> None:
    field = Field().sided()

    with field.drilling():
        field.pass_over()
        again, ended = field.pass_over(again=True)

    assert sorted(again) == sorted(f"D{n}" for n in range(WORDS))
    assert "pass is done" in ended


def test_a_session_nobody_spaced_writes_no_schedule() -> None:
    field = Field().sided()

    with field.drilling():
        field.pass_over()

    assert field.store.read(SCOPE, SCHEDULE) is None


def test_asking_for_spacing_writes_the_schedule() -> None:
    field = Field().sided()

    with field.drilling():
        word = field.tools["next_word"](spaced=True).split(" — ")[0]
        field.tools["how_it_went"](word=word, right=True)

    assert field.store.read(SCOPE, SCHEDULE) is not None


def test_spacing_asked_for_in_one_conversation_is_off_in_the_next() -> None:
    field = Field().sided()
    with field.drilling():
        word = field.tools["next_word"](spaced=True).split(" — ")[0]
        field.tools["how_it_went"](word=word, right=True)

    with field.drilling():
        word = field.tools["next_word"]().split(" — ")[0]
        said = field.tools["how_it_went"](word=word, right=True)

    assert "words still to put" in said


def test_the_side_asked_for_lasts_the_conversation_and_no_longer() -> None:
    field = Field(**{LISTED: PAIR}).sided()

    with field.drilling():
        first = field.tools["next_word"](put="other").split(" — ")[0]
        field.tools["how_it_went"](word=first, right=True)
        # Not passed again: the conversation remembers which way round it is running.
        second = field.tools["next_word"]().split(" — ")[0]

    with field.drilling():
        fresh = field.tools["next_word"]().split(" — ")[0]

    assert first in ENGLISH and second in ENGLISH
    assert fresh in GERMAN


def test_a_pass_needs_no_store_where_spacing_would() -> None:
    host = host_for(MODULE, files=FakeFiles({(SCOPE, LISTED): OTHER}))
    extend(host)
    tools = {e.value.name: e.value.run for e in host.registered if e.kind == TOOL}

    with keeping.bound({}), running_in(frozenset({SCOPE})):
        assert "Hund" in tools["next_word"]()
        with raises(ToolRefusal):
            tools["next_word"](spaced=True)
