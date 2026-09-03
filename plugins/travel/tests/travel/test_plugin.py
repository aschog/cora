import pytest

from cora.domain.errors import PluginLoadError
from cora.plugins.travel import CORPUS, INSTRUCTIONS, SCOPE, extend
from cora.plugins.travel.forecast import FORECAST_TOOL_NAME
from cora.plugins.travel.itinerary import ITINERARY_TOOL_NAME
from cora.plugins.travel.researcher import RESEARCH_TOOL_NAME
from cora.ports.host import INSTRUCTIONS as SAYS
from cora.ports.host import TOOL as HAS
from fakes import FakeOutput, host_for


def test_the_instructions_state_the_domains_own_business() -> None:
    """The persona cora carries is cora's; what this section adds is the field, what to
    cite, and the one thing a travel document is most often wrong about."""
    instructions = INSTRUCTIONS.lower()

    assert "travel" in instructions
    assert "cite" in instructions
    assert "out of date" in instructions
    assert "never invent" in instructions
    assert "offer to save" in instructions, (
        "the model offers the save; the gate is what happens next, not an excuse to "
        "announce a file as written"
    )


def test_everything_travel_registers_belongs_to_its_own_scope() -> None:
    """A travel persona has no business in a turn about training, and neither has a
    forecast: this plugin holds nothing it would want outside its field, so a turn
    about training is offered no way of reaching a weather service."""
    host = host_for("cora.plugins.travel", output=FakeOutput())

    extend(host)

    assert [(entry.kind, entry.scope) for entry in host.registered] == [
        (SAYS, SCOPE),
        (HAS, SCOPE),
        (HAS, SCOPE),
        (HAS, SCOPE),
    ]
    tools = [entry.value for entry in host.registered if entry.kind == HAS]
    assert [tool.name for tool in tools] == [
        FORECAST_TOOL_NAME,
        RESEARCH_TOOL_NAME,
        ITINERARY_TOOL_NAME,
    ]
    assert [tool.name for tool in tools if tool.effect] == [ITINERARY_TOOL_NAME], (
        "saving is the one thing here that changes something outside cora"
    )
    assert [tool.name for tool in tools if tool.untrusted] == [
        FORECAST_TOOL_NAME,
        RESEARCH_TOOL_NAME,
    ], "a service's answer is not cora's words, and neither is a report built on one"


def test_travel_offers_no_way_of_saving_where_a_deployment_configured_nowhere() -> None:
    """A tool the model can call and that always fails is worse than a tool it is never
    offered — the same reason cora offers no `remember` without a memory."""
    host = host_for("cora.plugins.travel")

    extend(host)

    tools = [entry.value for entry in host.registered if entry.kind == HAS]
    assert ITINERARY_TOOL_NAME not in [tool.name for tool in tools]


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


def test_a_rounds_setting_that_is_not_a_number_is_refused_by_name_at_load() -> None:
    """The operator is the audience for a load-time refusal, and they need the name of
    the setting they mistyped. A bare `ValueError` would reach them as "the plugin
    raised ValueError while registering" — cora keeps a plugin's exception text out of
    that message deliberately, because it could be carrying a key. So a plugin with
    something to tell the operator says it the sanctioned way, and that reaches them
    as it was worded."""
    host = host_for("cora.plugins.travel", settings={"rounds": "three"})

    with pytest.raises(PluginLoadError) as refused:
        extend(host)

    said = refused.value.user_message
    assert "rounds" in said, "the setting they can act on is named"
    assert "three" in said, "and what they set it to"
    assert "cora.plugins.travel" in said
