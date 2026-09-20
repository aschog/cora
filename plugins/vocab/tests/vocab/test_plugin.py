from cora.plugins.vocab import INSTRUCTIONS, SCOPE, extend
from cora.ports.host import INSTRUCTIONS as SAYS
from fakes import host_for


def test_the_field_is_a_voice_and_nothing_else() -> None:
    """A field that answers from its lists: searching them is cora's own tool, and the
    screen that writes one is cora's own, so the plugin brings neither."""
    host = host_for("cora.plugins.vocab")

    extend(host)

    assert [(entry.kind, entry.scope) for entry in host.registered] == [(SAYS, SCOPE)]


def test_the_instructions_say_what_the_field_answers_from() -> None:
    instructions = INSTRUCTIONS.lower()

    assert "vocabular" in instructions
    assert "cite" in instructions


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
    assert "german word that sounds like" in instructions
    assert "write the hint in german" in instructions
    assert "picture" in instructions
    assert "never the\n  answer" in instructions


def test_the_instructions_say_which_key_asks_for_a_hint() -> None:
    """One letter, and it has to be read as the ask rather than as an answer — which
    only holds if the field was told which letter it is."""
    instructions = INSTRUCTIONS.lower()

    assert "`h` on its own asks for a hint" in instructions
