"""The outer test for the card story.

The travel search is asked for with no route and no dates, so the tool puts its own
schema to the reader as a card. Nothing reaches the service until they submit it, and
what is priced is what they wrote. The network is the one thing stubbed.
"""

from typing import Any

import pytest
from starlette.testclient import TestClient

from app_builder import assembled
from cora.app.assembly import App
from cora.engine.steps import GATHERS
from cora.frontends.react.api import api
from cora.plugins.travel import SCOPE
from cora.plugins.travel.trips import (
    FLIGHTS_ASKED,
    FLIGHTS_TOOL_NAME,
    SEARCH_IT,
    SETTING,
    Search,
    trip_tools,
)
from cora.ports.chat_model import ModelReply
from cora.ports.host import Extension
from cora.ports.plugin import ToolCall
from fakes import ScriptedChatModel
from sse import frames

THREAD = "the-trip-i-have-not-planned"
QUESTION = "What is the cheapest way to get to Lisbon?"
ANSWER = "The cheapest week leaves 8 September, at 240 EUR return."
TRIP = {
    "origin": "BER",
    "destination": "LIS",
    "window_start": "2026-09-08",
    "window_end": "2026-09-15",
    "nights": 7,
}
FARES = {
    "best_flights": [
        {
            "price": 240,
            "flights": [{"departure_airport": {"id": "BER"}}],
            "total_duration": 190,
        }
    ]
}


class Service:
    """The fare service, written out — and a record of every query it was sent."""

    def __init__(self) -> None:
        self.queries: list[dict[str, Any]] = []

    def get(self, url: str, *, params: dict[str, Any]) -> "Service":
        self.queries.append(params)
        return self

    def raise_for_status(self) -> None:
        return None

    def json(self) -> Any:
        return FARES


def _underspecified() -> ModelReply:
    """The model asks for prices without saying where from, where to, or when."""
    return ModelReply(
        tool_calls=(
            ToolCall(
                name=FLIGHTS_TOOL_NAME, arguments={"destination": "LIS"}, call_id="f1"
            ),
        )
    )


@pytest.fixture
def service(monkeypatch: pytest.MonkeyPatch) -> Service:
    """Stubbed where the client is built, which is the one place the network is
    reached. The plugin, its registration and the whole turn are the real ones."""
    written = Service()
    monkeypatch.setattr(
        "cora.plugins.travel.trips._client", lambda: written, raising=True
    )
    return written


def _app(model: ScriptedChatModel) -> App:
    from cora.plugins.travel import extend

    return assembled(
        chat_model=model,
        plugins=(Extension(module="cora.plugins.travel", extend=extend),),
        scopes=(SCOPE,),
        plugin_settings={"cora.plugins.travel": {SETTING: "a-key"}},
    )


def _of(body: str, name: str) -> list[dict]:
    return [data for event, data in frames(body) if event == name]


def test_the_real_assembly_offers_the_search_with_nothing_required() -> None:
    """The whole point of the strip, through the app a deployment actually gets: the
    model is not told it must supply a route and a window before it may call."""
    model = ScriptedChatModel([ModelReply(text="ok")])
    _app(model).agent.answer("What is the cheapest way to Lisbon?", THREAD)

    offered = {tool.name: tool for tool in model.last_tools or ()}
    assert "required" not in offered[FLIGHTS_TOOL_NAME].parameter_schema
    assert offered[FLIGHTS_TOOL_NAME].parameter_schema["properties"]["origin"]
    assert GATHERS in offered[FLIGHTS_TOOL_NAME].description


def test_the_search_still_takes_exactly_what_it_always_took() -> None:
    """What the tool requires is unchanged: the card is built from the registered
    schema and every call is run against it, so the strip is the model's view alone."""
    [flights, _] = trip_tools(Search("a-key"))

    assert "origin" in flights.parameter_schema["required"]


def test_a_search_it_cannot_run_asks_me_for_the_trip_and_prices_what_i_give_it(
    service: Service,
) -> None:
    """The criterion: a card of the search's own fields, no request while it waits, and
    the values submitted are the ones the service is sent."""
    model = ScriptedChatModel([_underspecified(), ModelReply(text=ANSWER)])
    with TestClient(api(_app(model))) as reader:
        asked = reader.post(
            "/api/ask", json={"question": QUESTION, "thread_id": THREAD}
        )
        waiting = reader.get(f"/api/sessions/{THREAD}/pending").json()
        while_waiting = list(service.queries)
        submitted = reader.post(
            "/api/resume",
            json={"thread_id": THREAD, "answer": SEARCH_IT, "values": TRIP},
        )

    [paused] = _of(asked.text, "paused")
    card = paused["card"]
    assert paused["asked"] == QUESTION
    assert card["prompt"] == FLIGHTS_ASKED
    assert "origin" in [field["name"] for field in card["fields"]]
    assert all(field["editable"] for field in card["fields"])
    assert [action["answer"] for action in card["actions"]] == [SEARCH_IT, None]
    assert card["actions"][0]["needs_valid"], "a search runs on a trip, not on a blank"
    assert while_waiting == [], "nothing reached the service while the card waited"
    assert waiting["card"] == card, "a reload finds the same card"

    [turn] = _of(submitted.text, "turn")
    assert turn["answer"] == ANSWER
    [sent] = service.queries
    assert sent["departure_id"] == "BER"
    assert sent["arrival_id"] == "LIS"
    assert sent["outbound_date"] == "2026-09-08"
