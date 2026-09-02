from cora.plugins.travel import CORPUS, INSTRUCTIONS, SCOPE, extend
from cora.plugins.travel.forecast import FORECAST_TOOL_NAME
from cora.plugins.travel.researcher import RESEARCH_TOOL_NAME
from cora.ports.host import INSTRUCTIONS as SAYS
from cora.ports.host import TOOL as HAS
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
    """A travel persona has no business in a turn about training, and neither has a
    forecast: this plugin holds nothing it would want outside its field, so a turn
    about training is offered no way of reaching a weather service."""
    host = host_for("cora.plugins.travel")

    extend(host)

    assert [(entry.kind, entry.scope) for entry in host.registered] == [
        (SAYS, SCOPE),
        (HAS, SCOPE),
        (HAS, SCOPE),
    ]
    tools = [entry.value for entry in host.registered if entry.kind == HAS]
    assert [tool.name for tool in tools] == [FORECAST_TOOL_NAME, RESEARCH_TOOL_NAME]
    assert all(tool.untrusted for tool in tools), (
        "a service's answer is not cora's own words, and neither is a loop's report "
        "built out of one"
    )
    assert not any(tool.effect for tool in tools), (
        "travel changes nothing outside cora yet — its effect arrives with the gate"
    )


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
