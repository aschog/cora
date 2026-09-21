"""Which list a drill runs over, and how the reader comes to have chosen it.

The refusal is the mechanism: a model cannot skip a card it is told about in prose,
but it cannot get a word out of a tool that will not give one.
"""

from collections.abc import Iterator
from contextlib import contextmanager

from pytest import raises

from cora.engine import keeping
from cora.engine.scoping import running_in
from cora.plugins.vocab import SCOPE, extend
from cora.ports.host import TOOL
from cora.ports.plugin import ToolRefusal
from fakes import FakeFiles, FakeStore, host_for

MODULE = "cora.plugins.vocab"
ONE = "| Deutsch | English |\n| --- | --- |\n| Hund | dog |\n"
TWO = "| Deutsch | English |\n| --- | --- |\n| Apfel | apple |\n"
GERMAN, ENGLISH = ("Hund", "Apfel"), ("dog", "apple")


def _tools(**held: str) -> dict:
    files = {(SCOPE, name): text for name, text in held.items()}
    host = host_for(MODULE, files=FakeFiles(files), store=FakeStore())
    extend(host)
    tools = {e.value.name: e.value.run for e in host.registered if e.kind == TOOL}
    with keeping.bound({}), running_in(frozenset({SCOPE})):
        for name in held:
            tools["german_side"](name=name, side="left")
    return tools


@contextmanager
def drilling() -> Iterator[None]:
    with keeping.bound({}), running_in(frozenset({SCOPE})):
        yield


def test_two_lists_and_nothing_chosen_refuses_and_names_them() -> None:
    tools = _tools(**{"one.md": ONE, "two.md": TWO})

    with drilling(), raises(ToolRefusal) as refused:
        tools["next_word"]()

    assert "one.md" in str(refused.value)
    assert "two.md" in str(refused.value)
    assert "all of them" in str(refused.value)


def test_the_chosen_list_is_the_one_drilled() -> None:
    tools = _tools(**{"one.md": ONE, "two.md": TWO})

    with drilling():
        said = tools["next_word"](from_list="two.md")

    assert "Apfel" in said
    assert "Hund" not in said


def test_all_of_them_draws_from_both() -> None:
    tools = _tools(**{"one.md": ONE, "two.md": TWO})

    with drilling():
        first = tools["next_word"](from_list="*").split(" — ")[0]
        tools["how_it_went"](word=first, right=True)
        second = tools["next_word"]().split(" — ")[0]

    assert {first, second} == set(GERMAN)


def test_a_list_the_field_does_not_hold_is_refused_naming_the_ones_it_does() -> None:
    tools = _tools(**{"one.md": ONE})

    with drilling(), raises(ToolRefusal) as refused:
        tools["next_word"](from_list="nope.md")

    assert "nope.md" in str(refused.value)
    assert "one.md" in str(refused.value)


def test_one_list_is_drilled_without_anything_being_chosen() -> None:
    tools = _tools(**{"one.md": ONE})

    with drilling():
        assert "Hund" in tools["next_word"]()


def test_the_choice_is_asked_once_and_holds_for_the_conversation() -> None:
    tools = _tools(**{"one.md": ONE, "two.md": TWO})

    with drilling():
        first = tools["next_word"](from_list="two.md").split(" — ")[0]
        tools["how_it_went"](word=first, right=True)
        # Nothing chosen this time: the conversation is still on `two.md`, which has
        # one word, so the pass is done rather than refused.
        said = tools["next_word"]()

    assert first == "Apfel"
    assert "pass is done" in said


def test_another_conversation_chooses_again() -> None:
    tools = _tools(**{"one.md": ONE, "two.md": TWO})
    with drilling():
        tools["next_word"](from_list="two.md")

    with drilling(), raises(ToolRefusal):
        tools["next_word"]()


def test_choosing_again_in_one_conversation_replaces_what_was_chosen() -> None:
    tools = _tools(**{"one.md": ONE, "two.md": TWO})

    with drilling():
        tools["next_word"](from_list="two.md")
        said = tools["next_word"](from_list="one.md")

    assert "Hund" in said


def test_a_field_with_no_lists_says_so_rather_than_asking_which() -> None:
    tools = _tools()

    with drilling():
        assert "no word lists" in tools["next_word"]().lower()


# The side is settled per list, so a field of two asks about each of them in turn and
# the refusal carries enough of that list's pairs to be answered from.
def test_a_list_nobody_has_sided_is_refused_with_its_pairs() -> None:
    host = host_for(
        MODULE, files=FakeFiles({(SCOPE, "one.md"): ONE}), store=FakeStore()
    )
    extend(host)
    tools = {e.value.name: e.value.run for e in host.registered if e.kind == TOOL}

    with drilling(), raises(ToolRefusal) as refused:
        tools["next_word"]()

    assert "one.md" in str(refused.value)
    assert "Hund — dog" in str(refused.value)
    assert "german_side" in str(refused.value)


def test_the_side_of_a_list_outlives_the_conversation() -> None:
    tools = _tools(**{"one.md": ONE})

    with drilling():
        assert "Hund" in tools["next_word"]()

    with drilling():
        assert "Hund" in tools["next_word"]()


# The store is one plugin's, not one field's, so two fields holding a same-named list
# must not share the answer. They are told apart by the list itself.
def test_two_lists_of_one_name_each_answer_for_their_own_column() -> None:
    store = FakeStore()
    here = host_for(MODULE, files=FakeFiles({(SCOPE, "unit.md"): ONE}), store=store)
    extend(here)
    mine = {e.value.name: e.value.run for e in here.registered if e.kind == TOOL}
    with drilling():
        mine["german_side"](name="unit.md", side="left")

    there = host_for(
        "cora.plugins.vocab",
        files=FakeFiles(
            {("spanish", "unit.md"): "| a | b |\n| - | - |\n| casa | Haus |\n"}
        ),
        store=store,
    )
    extend(there)
    theirs = {e.value.name: e.value.run for e in there.registered if e.kind == TOOL}

    with keeping.bound({}), running_in(frozenset({"spanish"})), raises(ToolRefusal):
        theirs["next_word"]()
