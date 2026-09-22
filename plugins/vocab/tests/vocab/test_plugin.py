from cora.plugins.vocab import INSTRUCTIONS, SCOPE, extend
from cora.ports.host import ANSWERING, HANDLER, TAKING, TOOL
from cora.ports.host import INSTRUCTIONS as SAYS
from fakes import host_for


def test_the_field_is_a_voice_five_calls_and_two_hands_on_the_turn() -> None:
    host = host_for("cora.plugins.vocab")

    extend(host)

    assert [(entry.kind, entry.scope) for entry in host.registered] == [
        (SAYS, SCOPE),
        *[(TOOL, SCOPE)] * 4,
        (HANDLER, SCOPE),
        (HANDLER, SCOPE),
        (TOOL, SCOPE),
    ]
    assert [
        entry.value.event for entry in host.registered if entry.kind == HANDLER
    ] == [ANSWERING, TAKING]
    assert [entry.value.name for entry in host.registered if entry.kind == TOOL] == [
        "find_word",
        "show_list",
        "german_side",
        "next_word",
        "how_it_went",
    ]


def test_the_instructions_say_what_the_field_answers_from() -> None:
    instructions = INSTRUCTIONS.lower()

    assert "vocabular" in instructions
    assert "find_word" in instructions


def test_the_instructions_keep_the_answers_back_while_practising() -> None:
    instructions = INSTRUCTIONS.lower()

    assert "one word at a time" in instructions
    assert "do not show" in instructions


def test_the_instructions_say_a_hint_is_a_clue_in_the_readers_own_language() -> None:
    instructions = INSTRUCTIONS.lower()

    assert "hint" in instructions
    assert "the word the reader has to produce" in instructions
    assert "german word that sounds like" in instructions
    assert "write the hint in german" in instructions
    assert "picture" in instructions
    assert "never the\n  answer" in instructions


def test_the_instructions_say_which_key_asks_for_a_hint() -> None:
    instructions = INSTRUCTIONS.lower()

    assert "`h` on its own asks for a hint" in instructions


def test_the_instructions_drill_through_the_tools() -> None:
    instructions = INSTRUCTIONS.lower()

    assert "next_word" in instructions
    assert "how_it_went" in instructions
    assert "never pick a word yourself" in instructions


def test_the_instructions_say_a_right_answer_never_reaches_the_model() -> None:
    instructions = INSTRUCTIONS.lower()

    assert "a right answer never reaches you" in instructions
    assert "the word on the table is the last one put" in instructions
