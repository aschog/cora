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
