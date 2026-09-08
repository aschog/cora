from cora.plugins.travel import CORPUS, SCOPE, extend
from cora.plugins.travel.forecast import FORECAST_TOOL_NAME
from cora.plugins.travel.itinerary import ITINERARY_TOOL_NAME
from cora.plugins.travel.planner import PLAN_TOOL_NAME, REVISE_TOOL_NAME
from cora.plugins.travel.researcher import RESEARCH_TOOL_NAME
from cora.plugins.travel.trips import (
    FLIGHTS_TOOL_NAME,
    HOTELS_TOOL_NAME,
    SETTING,
)
from cora.ports.host import TOOL as HAS
from fakes import FakeOutput, host_for


def test_everything_travel_registers_belongs_to_its_own_scope() -> None:
    """A travel persona has no business in a turn about training, and neither has a
    forecast: this plugin holds nothing it would want outside its field, so a turn
    about training is offered no way of reaching a weather service."""
    host = host_for("cora.plugins.travel", output=FakeOutput())

    extend(host)

    assert {entry.scope for entry in host.registered} == {SCOPE}
    tools = [entry.value for entry in host.registered if entry.kind == HAS]
    assert [tool.name for tool in tools] == [
        FORECAST_TOOL_NAME,
        RESEARCH_TOOL_NAME,
        PLAN_TOOL_NAME,
        REVISE_TOOL_NAME,
        ITINERARY_TOOL_NAME,
    ]
    assert [tool.name for tool in tools if tool.effect] == [ITINERARY_TOOL_NAME], (
        "saving is the one thing here that changes something outside cora"
    )
    assert [tool.name for tool in tools if tool.untrusted] == [
        FORECAST_TOOL_NAME,
        RESEARCH_TOOL_NAME,
        PLAN_TOOL_NAME,
        REVISE_TOOL_NAME,
    ], "a service's answer is not cora's words, and neither is a plan built on one"


def test_travel_offers_no_way_of_saving_where_a_deployment_configured_nowhere() -> None:
    """A tool the model can call and that always fails is worse than a tool it is never
    offered — the same reason cora offers no `remember` without a memory."""
    host = host_for("cora.plugins.travel")

    extend(host)

    tools = [entry.value for entry in host.registered if entry.kind == HAS]
    assert ITINERARY_TOOL_NAME not in [tool.name for tool in tools]


def test_the_corpus_ships_as_documents_a_reader_can_upload() -> None:
    """Routing needs a field with something in it. Files rather than a registration:
    a plugin that seeded the index at load would re-embed its notes on every start."""
    shipped = sorted(path.name for path in CORPUS.glob("*.md"))

    assert shipped
    assert all(path.read_text().strip() for path in CORPUS.glob("*.md"))


def test_travel_offers_no_prices_where_a_deployment_set_no_key() -> None:
    """The same rule saving follows: a tool the model can call and that can only fail
    is worse than one it is never offered."""
    host = host_for("cora.plugins.travel", output=FakeOutput())

    extend(host)

    tools = [entry.value.name for entry in host.registered if entry.kind == HAS]
    assert FLIGHTS_TOOL_NAME not in tools
    assert HOTELS_TOOL_NAME not in tools
    assert FORECAST_TOOL_NAME in tools, "what needs no key is unaffected"


def test_both_searches_arrive_in_travels_own_field_once_a_key_is_set() -> None:
    host = host_for(
        "cora.plugins.travel", output=FakeOutput(), settings={SETTING: "a-key"}
    )

    extend(host)

    priced = [
        entry
        for entry in host.registered
        if entry.kind == HAS
        and entry.value.name in (FLIGHTS_TOOL_NAME, HOTELS_TOOL_NAME)
    ]
    assert [entry.value.name for entry in priced] == [
        FLIGHTS_TOOL_NAME,
        HOTELS_TOOL_NAME,
    ]
    assert [entry.scope for entry in priced] == [SCOPE, SCOPE], (
        "a turn about training is offered no prices"
    )
    assert all(entry.value.untrusted for entry in priced)
    assert not any(entry.value.effect for entry in priced), "neither buys anything"
