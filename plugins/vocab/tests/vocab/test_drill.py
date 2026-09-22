import datetime
from collections.abc import Iterator
from contextlib import contextmanager

from pytest import raises

from cora.engine import keeping
from cora.engine.scoping import running_in
from cora.plugins.vocab import SCHEDULE, SCOPE, extend
from cora.plugins.vocab.schedule import Schedule
from cora.plugins.vocab.sm2 import Card
from cora.ports.host import TOOL
from cora.ports.plugin import ToolRefusal
from fakes import FakeFiles, FakeStore, host_for

MODULE = "cora.plugins.vocab"
LIST = """# English — Einheit 3

| Deutsch | English |
| --- | --- |
| Hilfe | help |
| Haus | house |
"""
READ = "1. Apple — Apfel\n2. Book — Buch\n"
# One pair, for the tests about how a word is put rather than about which: a pass with
# spacing off shuffles, so a list of two has no first word to assert on.
ONE = "| Deutsch | English |\n| --- | --- |\n| Hilfe | help |\n"
ONE_READ = "1. Apple — Apfel\n"
TODAY = datetime.date.today()
LISTED = "einheit-3.md"


@contextmanager
def drilling() -> Iterator[None]:
    with keeping.bound({}), running_in(frozenset({SCOPE})):
        yield


def _drill(
    held: str = LIST, kept: str | None = None, german: str | None = "left"
) -> tuple[dict, FakeStore]:
    # `german` is which column of `held` holds it, said once as the model says it;
    # `None` is a fixture with no pairs in it, which there is nothing to say about.
    store = FakeStore()
    if kept is not None:
        store.keep("vocab", SCHEDULE, kept)
    host = host_for(
        MODULE,
        files=FakeFiles({(SCOPE, LISTED): held}),
        store=store,
    )
    extend(host)
    tools = {
        entry.value.name: entry.value.run
        for entry in host.registered
        if entry.kind == TOOL
    }
    if german is not None:
        with drilling():
            tools["german_side"](name=LISTED, side=german)
    return tools, store


def test_only_this_fields_files_are_drilled() -> None:
    store = FakeStore()
    host = host_for(
        MODULE,
        files=FakeFiles({("notes", "elsewhere.md"): READ, (SCOPE, LISTED): LIST}),
        store=store,
    )
    extend(host)
    tools = {
        entry.value.name: entry.value.run
        for entry in host.registered
        if entry.kind == TOOL
    }

    with drilling():
        tools["german_side"](name=LISTED, side="left")
        asked = tools["next_word"]()

    assert "Hilfe" in asked or "Haus" in asked
    assert "Apple" not in asked


def test_a_word_is_put_from_the_side_asked_and_not_the_other() -> None:
    tools, _ = _drill(held=ONE)

    with drilling():
        asked = tools["next_word"]()

    assert "Hilfe" in asked
    assert "help" not in asked


def test_the_other_way_round_puts_the_other_side() -> None:
    tools, _ = _drill(held=ONE)

    with drilling():
        asked = tools["next_word"](put="other")

    assert "help" in asked
    assert "Hilfe" not in asked


def test_a_word_put_says_which_list_and_which_side_it_came_from() -> None:
    tools, _ = _drill(held=ONE)

    with drilling():
        asked = tools["next_word"]()

    assert "einheit-3.md" in asked
    assert "English" in asked


def test_a_list_read_out_of_a_screenshot_is_drilled_like_any_other() -> None:
    tools, _ = _drill(held=ONE_READ, german="right")

    with drilling():
        asked = tools["next_word"]()

    # The German is put whichever column it landed in, which for a screenshot of an
    # English-first page is the right one.
    assert "Apfel" in asked
    assert "Apple" not in asked


def test_a_word_that_is_due_is_preferred_to_one_that_is_not() -> None:
    kept = Schedule().with_card(
        "Hilfe|help", Card(due=TODAY + datetime.timedelta(days=6), interval=6, right=2)
    )
    tools, _ = _drill(kept=kept.written())

    with drilling():
        asked = tools["next_word"](spaced=True)

    assert "Haus" in asked


def test_a_word_already_missed_is_put_before_a_word_never_drilled() -> None:
    kept = Schedule().with_card("Haus|house", Card(due=TODAY, interval=0, right=0))
    tools, _ = _drill(kept=kept.written())

    with drilling():
        asked = tools["next_word"](spaced=True)

    assert "Haus" in asked


def test_nothing_due_and_nothing_new_says_the_session_is_done() -> None:
    later = TODAY + datetime.timedelta(days=6)
    kept = (
        Schedule()
        .with_card("Hilfe|help", Card(due=later, interval=6, right=2))
        .with_card("Haus|house", Card(due=later, interval=6, right=2))
    )
    tools, _ = _drill(kept=kept.written())

    with drilling():
        said = tools["next_word"](spaced=True)

    assert "done" in said.lower()


def test_saying_how_it_went_moves_that_words_schedule_in_the_store() -> None:
    tools, store = _drill(held=ONE)

    with drilling():
        tools["next_word"](spaced=True)
        tools["how_it_went"](word="Hilfe", right=True)

    kept = Schedule.of(store.read("vocab", SCHEDULE))
    assert kept.card("Hilfe|help").due == TODAY + datetime.timedelta(days=1)
    assert kept.card("Haus|house") == Card(), "the word nobody answered is where it was"


def test_a_missed_word_is_the_word_put_next() -> None:
    tools, _ = _drill(held=ONE)

    with drilling():
        tools["next_word"](spaced=True)
        tools["how_it_went"](word="Hilfe", right=False)
        again = tools["next_word"](spaced=True)

    assert "Hilfe" in again


def test_the_answer_is_taken_for_the_word_that_was_put_either_side() -> None:
    tools, store = _drill(held=ONE)

    with drilling():
        tools["next_word"](spaced=True)
        tools["how_it_went"](word="help", right=True)

    assert Schedule.of(store.read("vocab", SCHEDULE)).card("Hilfe|help").right == 1


def test_saying_how_a_word_nobody_asked_about_went_is_refused() -> None:
    tools, store = _drill()

    with drilling(), raises(ToolRefusal):
        tools["how_it_went"](word="Haus", right=True)

    assert store.read("vocab", SCHEDULE) is None


def test_a_field_holding_no_list_says_so() -> None:
    tools, _ = _drill(held="Just some prose about words.", german=None)

    with drilling():
        assert "no word lists" in tools["next_word"]().lower()


def test_a_spaced_drill_with_no_store_says_so_rather_than_drilling_into_nothing() -> (
    None
):
    host = host_for(
        MODULE,
        files=FakeFiles({(SCOPE, LISTED): LIST}),
    )
    extend(host)
    tools = {
        entry.value.name: entry.value.run
        for entry in host.registered
        if entry.kind == TOOL
    }

    with drilling():
        assert "einheit-3.md" in tools["next_word"]()

    with drilling(), raises(ToolRefusal):
        tools["next_word"](spaced=True)
