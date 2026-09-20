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
READ = "1. Apple — Apfel\n2. Book — Buch\n"
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


def test_only_this_fields_documents_are_drilled() -> None:
    """A turn can run over more than one field, and `documents.all()` hands over every
    document of every field it is running in. A note in another field is not vocabulary
    this plugin may put to the reader."""
    store = FakeStore()
    host = host_for(
        MODULE,
        documents=FakeContextSource(
            held=[
                Document(name="elsewhere.md", text=READ, scope="notes"),
                Document(name="einheit-3.md", text=LIST, scope=SCOPE),
            ]
        ),
        store=store,
    )
    extend(host)
    tools = {
        entry.value.name: entry.value.run
        for entry in host.registered
        if entry.kind == TOOL
    }

    with keeping.bound({}):
        asked = tools["next_word"]()

    assert "Hilfe" in asked
    assert "Apple" not in asked


def test_a_word_is_put_from_the_side_asked_and_not_the_other() -> None:
    tools, _ = _drill()

    with keeping.bound({}):
        asked = tools["next_word"]()

    assert "Hilfe" in asked
    assert "help" not in asked


def test_the_other_way_round_puts_the_other_side() -> None:
    tools, _ = _drill()

    with keeping.bound({}):
        asked = tools["next_word"](side="right")

    assert "help" in asked
    assert "Hilfe" not in asked


def test_a_word_put_says_which_list_and_which_side_it_came_from() -> None:
    """The model has to tell the reader what it is asking for, and a table says what
    its two columns are called."""
    tools, _ = _drill()

    with keeping.bound({}):
        asked = tools["next_word"]()

    assert "einheit-3.md" in asked
    assert "English" in asked


def test_a_list_read_out_of_a_screenshot_is_drilled_like_any_other() -> None:
    """The regression this was found by: a list the reading saved is lines rather than
    a table, and the drill said the field held no lists at all."""
    tools, _ = _drill(held=READ)

    with keeping.bound({}):
        asked = tools["next_word"]()

    assert "Apple" in asked
    assert "Apfel" not in asked


def test_a_word_that_is_due_is_preferred_to_one_that_is_not() -> None:
    kept = Schedule().with_card(
        "Hilfe|help", Card(due=TODAY + datetime.timedelta(days=6), interval=6, right=2)
    )
    tools, _ = _drill(kept=kept.written())

    with keeping.bound({}):
        asked = tools["next_word"]()

    assert "Haus" in asked


def test_a_word_already_missed_is_put_before_a_word_never_drilled() -> None:
    """What a session is for is the words that did not stick. New ones fill it up
    afterwards."""
    kept = Schedule().with_card("Haus|house", Card(due=TODAY, interval=0, right=0))
    tools, _ = _drill(kept=kept.written())

    with keeping.bound({}):
        asked = tools["next_word"]()

    assert "Haus" in asked


def test_nothing_due_and_nothing_new_says_the_session_is_done() -> None:
    later = TODAY + datetime.timedelta(days=6)
    kept = (
        Schedule()
        .with_card("Hilfe|help", Card(due=later, interval=6, right=2))
        .with_card("Haus|house", Card(due=later, interval=6, right=2))
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
    assert kept.card("Hilfe|help").due == TODAY + datetime.timedelta(days=1)
    assert kept.card("Haus|house") == Card(), "the word nobody answered is where it was"


def test_a_missed_word_is_the_word_put_next() -> None:
    tools, _ = _drill()

    with keeping.bound({}):
        tools["next_word"]()
        tools["how_it_went"](word="Hilfe", right=False)
        again = tools["next_word"]()

    assert "Hilfe" in again


def test_the_answer_is_taken_for_the_word_that_was_put_either_side() -> None:
    """The model reports the word it put, and a model reporting the answer instead is
    talking about the same card."""
    tools, store = _drill()

    with keeping.bound({}):
        tools["next_word"]()
        tools["how_it_went"](word="help", right=True)

    assert Schedule.of(store.read("vocab", SCHEDULE)).card("Hilfe|help").right == 1


def test_saying_how_a_word_nobody_asked_about_went_is_refused() -> None:
    """The schedule moves on what the reader answered, and the model is what reports
    that — so a word it names that nothing asked is refused rather than written."""
    tools, store = _drill()

    with keeping.bound({}), raises(ToolRefusal):
        tools["how_it_went"](word="Haus", right=True)

    assert store.read("vocab", SCHEDULE) is None


def test_a_field_holding_no_list_says_so() -> None:
    tools, _ = _drill(held="Just some prose about words.")

    with keeping.bound({}):
        assert "no word lists" in tools["next_word"]().lower()


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
