import datetime

from pytest import raises

from cora.engine import keeping
from cora.plugins.vocab import SCHEDULE, SCOPE, extend
from cora.plugins.vocab.schedule import Schedule
from cora.plugins.vocab.sm2 import Card
from cora.ports.context_source import Document
from cora.ports.host import TOOL
from cora.ports.plugin import ToolRefusal
from fakes import FakeContextSource, FakeStore, host_for

MODULE = "cora.plugins.vocab"
LIST = """# English — Einheit 3

| Deutsch | English |
| --- | --- |
| Hilfe | help |
| Haus | house |
"""
TODAY = datetime.date.today()


def _drill(held: str = LIST, kept: str | None = None) -> tuple[dict, FakeStore]:
    store = FakeStore()
    if kept is not None:
        store.keep("vocab", SCHEDULE, kept)
    host = host_for(
        MODULE,
        documents=FakeContextSource(
            held=[Document(name="einheit-3.md", text=held, scope=SCOPE)]
        ),
        store=store,
    )
    extend(host)
    tools = {
        entry.value.name: entry.value.run
        for entry in host.registered
        if entry.kind == TOOL
    }
    return tools, store


def test_a_word_is_put_from_the_side_being_asked_and_not_the_other() -> None:
    tools, _ = _drill()

    with keeping.bound({}):
        asked = tools["next_word"]()

    assert "Hilfe" in asked
    assert "help" not in asked


def test_the_other_way_round_puts_the_word_being_learnt() -> None:
    tools, _ = _drill()

    with keeping.bound({}):
        asked = tools["next_word"](direction="from_learning")

    assert "help" in asked
    assert "Hilfe" not in asked


def test_a_word_that_is_due_is_preferred_to_one_that_is_not() -> None:
    kept = Schedule().with_card(
        "help", Card(due=TODAY + datetime.timedelta(days=6), interval=6, right=2)
    )
    tools, _ = _drill(kept=kept.written())

    with keeping.bound({}):
        asked = tools["next_word"]()

    assert "Haus" in asked


def test_nothing_due_and_nothing_new_says_the_session_is_done() -> None:
    later = TODAY + datetime.timedelta(days=6)
    kept = (
        Schedule()
        .with_card("help", Card(due=later, interval=6, right=2))
        .with_card("house", Card(due=later, interval=6, right=2))
    )
    tools, _ = _drill(kept=kept.written())

    with keeping.bound({}):
        said = tools["next_word"]()

    assert "done" in said.lower()


def test_saying_how_it_went_moves_that_words_schedule_in_the_store() -> None:
    tools, store = _drill()

    with keeping.bound({}):
        tools["next_word"]()
        tools["how_it_went"](word="Hilfe", right=True)

    kept = Schedule.of(store.read("vocab", SCHEDULE))
    assert kept.card("help").due == TODAY + datetime.timedelta(days=1)
    assert kept.card("house") == Card(), "the word nobody answered is where it was"


def test_a_missed_word_is_the_word_put_next() -> None:
    tools, _ = _drill()

    with keeping.bound({}):
        tools["next_word"]()
        tools["how_it_went"](word="Hilfe", right=False)
        again = tools["next_word"]()

    assert "Hilfe" in again


def test_saying_how_a_word_nobody_asked_about_went_is_refused() -> None:
    """The schedule moves on what the reader answered, and the model is what reports
    that — so a word it names that nothing asked is refused rather than written."""
    tools, store = _drill()

    with keeping.bound({}), raises(ToolRefusal):
        tools["how_it_went"](word="Haus", right=True)

    assert store.read("vocab", SCHEDULE) is None


def test_a_field_with_no_store_says_so_rather_than_drilling_into_nothing() -> None:
    host = host_for(
        MODULE,
        documents=FakeContextSource(
            held=[Document(name="einheit-3.md", text=LIST, scope=SCOPE)]
        ),
    )
    extend(host)
    tools = {
        entry.value.name: entry.value.run
        for entry in host.registered
        if entry.kind == TOOL
    }

    with keeping.bound({}), raises(ToolRefusal):
        tools["next_word"]()


def test_a_word_already_missed_is_put_before_a_word_never_drilled() -> None:
    """What a session is for is the words that did not stick. New ones fill it up
    afterwards."""
    kept = Schedule().with_card("house", Card(due=TODAY, interval=0, right=0))
    tools, _ = _drill(kept=kept.written())

    with keeping.bound({}):
        asked = tools["next_word"]()

    assert "Haus" in asked
