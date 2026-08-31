from cora.plugins.travel import CORPUS, INSTRUCTIONS, SCOPE, extend
from cora.ports.host import INSTRUCTIONS as SAYS
from fakes import host_for


def test_the_instructions_state_the_domains_own_business() -> None:
    """The persona cora carries is cora's; what this section adds is the field, what to
    cite, and the one thing a travel document is most often wrong about."""
    instructions = INSTRUCTIONS.lower()

    assert "travel" in instructions
    assert "cite" in instructions
    assert "out of date" in instructions
    assert "never invent" in instructions


def test_everything_travel_registers_belongs_to_its_own_scope() -> None:
    """A travel persona has no business in a turn about training, and this plugin has
    nothing it would want to hold outside its field: no tool yet, and nothing
    system-wide."""
    host = host_for("cora.plugins.travel")

    extend(host)

    assert [(entry.kind, entry.scope) for entry in host.registered] == [(SAYS, SCOPE)]


def test_the_first_line_of_the_instructions_says_what_the_field_is() -> None:
    """It is what the router is given to choose between, and what the card that asks the
    user says under the name — so a first line that opened with a rule would route on
    the rule."""
    [first, *_] = INSTRUCTIONS.splitlines()

    assert "travel" in first.lower()


def test_the_corpus_ships_as_documents_a_reader_can_upload() -> None:
    """Routing needs a field with something in it. Files rather than a registration:
    a plugin that seeded the index at load would re-embed its notes on every start."""
    shipped = sorted(path.name for path in CORPUS.glob("*.md"))

    assert shipped
    assert all(path.read_text().strip() for path in CORPUS.glob("*.md"))
