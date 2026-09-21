"""The check on the answer: a word the drill never put never reaches the reader.

Driven through the real answering step, because the bug this guards against is one of
where the check runs — a model that stops calling the tools and writes the next word
out of its own head. The step runs handlers outside any tool call, so the check has no
plugin state to read, and these tests would pass over a version that relied on it.
"""

from collections.abc import Iterator
from contextlib import contextmanager

from cora.engine import keeping
from cora.engine.plugin_set import Registry
from cora.engine.scoping import running_in
from cora.engine.steps import AnswerStep
from cora.plugins.vocab import SCOPE, extend
from cora.ports.chat_model import Message
from cora.ports.host import TOOL
from fakes import FakeFiles, FakeStore, host_for

MODULE = "cora.plugins.vocab"
UNIT = (
    "| Deutsch | English |\n| --- | --- |\n"
    "| Apfel | apple |\n| Hund | dog |\n| Haus | house |\n"
)
LISTED = "unit.md"


class Field:
    """One vocab field, its tools, and the step that settles what the reader is told."""

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
        self.step = AnswerStep(registry=Registry(tuple(host.registered)))

    @contextmanager
    def drilling(self) -> Iterator[None]:
        with keeping.bound({}), running_in(frozenset({SCOPE})):
            yield

    def put(self) -> str:
        with self.drilling():
            self.tools["german_side"](name=LISTED, side="left")
            self.tools["next_word"]()
        return self.drill.current.shown

    def answers(self, written: str) -> str:
        settled = self.step(
            {
                "messages": [
                    Message(role="user", content="…"),
                    Message(role="assistant", content=written),
                ],
                "turn_start": 0,
                "scopes": [SCOPE],
            }
        )
        return settled["answer"]


def test_a_word_from_nowhere_is_replaced_by_the_word_on_the_table() -> None:
    field = Field()
    shown = field.put()

    assert field.answers(f"{shown}baum") == shown


def test_the_word_on_the_table_is_left_alone() -> None:
    field = Field()
    shown = field.put()

    assert field.answers(shown) == shown


def test_markup_around_the_word_on_the_table_is_left_alone() -> None:
    field = Field()
    shown = field.put()

    assert field.answers(f"**{shown}**") == f"**{shown}**"


# A reader answering the word they were asked for, in the other language: it is on the
# list, so it is not a word from nowhere.
def test_a_word_from_the_list_is_left_alone() -> None:
    field = Field()
    field.put()

    assert field.answers("house") == "house"


def test_a_sentence_is_left_alone() -> None:
    field = Field()
    field.put()

    said = "Das heißt auf Englisch „apple“."
    assert field.answers(said) == said


def test_nothing_on_the_table_leaves_every_answer_alone() -> None:
    field = Field()

    assert field.answers("Apfelbaum") == "Apfelbaum"


def test_a_word_answered_for_leaves_the_next_answer_alone() -> None:
    field = Field()
    shown = field.put()
    with field.drilling():
        field.tools["how_it_went"](word=shown, right=True)

    assert field.answers("Apfelbaum") == "Apfelbaum"


# The check runs where no tool call does, so it must not pop a word, reshuffle the
# pass, or touch what the conversation kept. An earlier version called `next_word`
# from inside it and silently threw the reader's progress away.
def test_the_check_takes_nothing_off_the_pass() -> None:
    field = Field()
    shown = field.put()
    before = list(field.drill.current.queue)

    field.answers(f"{shown}baum")

    assert field.drill.current.queue == before
    assert field.drill.current.shown == shown


def test_the_check_leaves_the_word_on_the_table_to_be_answered() -> None:
    field = Field()
    shown = field.put()

    field.answers("Erfunden")

    with field.drilling():
        assert "still to put" in field.tools["how_it_went"](word=shown, right=True)


def test_a_field_of_two_lists_still_checks_the_answer() -> None:
    host = host_for(
        MODULE,
        files=FakeFiles({(SCOPE, "one.md"): UNIT, (SCOPE, "two.md"): UNIT}),
        store=FakeStore(),
    )
    extend(host)
    tools = {e.value.name: e.value.run for e in host.registered if e.kind == TOOL}
    step = AnswerStep(registry=Registry(tuple(host.registered)))
    with keeping.bound({}), running_in(frozenset({SCOPE})):
        tools["german_side"](name="one.md", side="left")
        tools["next_word"](from_list="one.md")
    shown = tools["next_word"].__self__.current.shown

    settled = step(
        {
            "messages": [
                Message(role="user", content="…"),
                Message(role="assistant", content="Erfunden"),
            ],
            "turn_start": 0,
            "scopes": [SCOPE],
        }
    )

    assert settled["answer"] == shown
