from cora.plugins.vocab import INSTRUCTIONS, SCOPE, extend
from cora.ports.host import INSTRUCTIONS as SAYS
from cora.ports.host import TOOL
from fakes import host_for


def test_the_field_is_a_voice_and_the_four_calls_it_runs_on() -> None:
    """The screen that writes a list is cora's own, so what the plugin brings is
    reading its lists — nothing indexes a file — and the spacing over them."""
    host = host_for("cora.plugins.vocab")

    extend(host)

    assert [(entry.kind, entry.scope) for entry in host.registered] == [
        (SAYS, SCOPE),
        (TOOL, SCOPE),
        (TOOL, SCOPE),
        (TOOL, SCOPE),
        (TOOL, SCOPE),
    ]
    assert [entry.value.name for entry in host.registered if entry.kind == TOOL] == [
        "find_word",
        "show_list",
        "next_word",
        "how_it_went",
    ]


def test_the_instructions_say_what_the_field_answers_from() -> None:
    instructions = INSTRUCTIONS.lower()

    assert "vocabular" in instructions
    assert "find_word" in instructions


def test_the_instructions_keep_the_answers_back_while_practising() -> None:
    """A drill whose answers are on the screen is a reading exercise: what the field is
    for is the word the reader has to produce, so the other half stays hidden."""
    instructions = INSTRUCTIONS.lower()

    assert "one word at a time" in instructions
    assert "do not show" in instructions


def test_the_instructions_say_a_hint_is_a_clue_in_the_readers_own_language() -> None:
    """A hint spelled out of the word being practised hands over the answer a letter at
    a time. What the reader gets instead is a sound they already know and a picture
    hung on it, and the word stays theirs to produce."""
    instructions = INSTRUCTIONS.lower()

    assert "hint" in instructions
    assert "the word the reader has to produce" in instructions
    assert "german word that sounds like" in instructions
    assert "write the hint in german" in instructions
    assert "picture" in instructions
    assert "never the\n  answer" in instructions


def test_the_instructions_say_which_key_asks_for_a_hint() -> None:
    """One letter, and it has to be read as the ask rather than as an answer — which
    only holds if the field was told which letter it is."""
    instructions = INSTRUCTIONS.lower()

    assert "`h` on its own asks for a hint" in instructions


def test_the_instructions_drill_through_the_tools() -> None:
    """The spacing is arithmetic and the model is not to do it: which word comes when
    is the schedule's, as the fitness field's numbers are its calculators'."""
    instructions = INSTRUCTIONS.lower()

    assert "next_word" in instructions
    assert "how_it_went" in instructions
    assert "never pick a word yourself" in instructions
