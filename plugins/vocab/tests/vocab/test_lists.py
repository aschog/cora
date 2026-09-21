"""Reading the lists out loud, now that nothing indexes them."""

from collections.abc import Iterator
from contextlib import contextmanager

from cora.engine import keeping
from cora.engine.scoping import running_in
from cora.plugins.vocab import SCOPE, extend
from cora.ports.host import TOOL
from fakes import FakeFiles, FakeStore, host_for

MODULE = "cora.plugins.vocab"
UNIT = "| Deutsch | English |\n| --- | --- |\n| Hilfe | help |\n| Haus | house |\n"
READ = "Apple — Apfel\nBook — Buch\n"


@contextmanager
def reading() -> Iterator[None]:
    with keeping.bound({}), running_in(frozenset({SCOPE})):
        yield


def _tools(**held: str) -> dict:
    files = {(SCOPE, name): text for name, text in held.items()}
    host = host_for(MODULE, files=FakeFiles(files), store=FakeStore())
    extend(host)
    return {e.value.name: e.value.run for e in host.registered if e.kind == TOOL}


def test_a_word_is_found_with_the_list_it_is_on() -> None:
    tools = _tools(**{"unit.md": UNIT})

    with reading():
        said = tools["find_word"](word="help")

    assert "Hilfe" in said
    assert "unit.md" in said


def test_a_word_is_found_from_either_side() -> None:
    tools = _tools(**{"unit.md": UNIT})

    with reading():
        assert "help" in tools["find_word"](word="Hilfe")


def test_a_word_on_no_list_is_said_to_be_on_none() -> None:
    tools = _tools(**{"unit.md": UNIT})

    with reading():
        said = tools["find_word"](word="Fahrrad")

    assert "none of the lists" in said
    assert "Fahrrad" in said


def test_a_word_on_two_lists_names_both() -> None:
    tools = _tools(**{"one.md": UNIT, "two.md": UNIT})

    with reading():
        said = tools["find_word"](word="help")

    assert "one.md" in said
    assert "two.md" in said


def test_a_field_with_no_lists_says_so_rather_than_finding_nothing() -> None:
    tools = _tools()

    with reading():
        assert "no word lists" in tools["find_word"](word="help").lower()
        assert "no word lists" in tools["show_list"]().lower()


def test_show_list_with_no_name_gives_the_names() -> None:
    tools = _tools(**{"one.md": UNIT, "two.md": READ})

    with reading():
        said = tools["show_list"]()

    assert said.splitlines() == ["one.md", "two.md"]


def test_show_list_named_gives_that_list_whole() -> None:
    tools = _tools(**{"one.md": UNIT, "two.md": READ})

    with reading():
        said = tools["show_list"](name="one.md")

    assert "Hilfe — help" in said
    assert "Apple" not in said


def test_a_list_the_field_does_not_hold_names_the_ones_it_does() -> None:
    tools = _tools(**{"one.md": UNIT})

    with reading():
        said = tools["show_list"](name="nope.md")

    assert "no list called 'nope.md'" in said
    assert "one.md" in said


# A file the field holds that is not a list of pairs contributes nothing, rather than
# breaking the reading of the lists that are.
def test_a_file_that_is_not_a_list_is_not_one() -> None:
    tools = _tools(**{"one.md": UNIT, "notes.md": "Just some prose about words."})

    with reading():
        assert tools["show_list"]().splitlines() == ["one.md"]
