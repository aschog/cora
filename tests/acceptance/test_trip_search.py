"""The outer test for the priced trip search.

The whole path the plugin really ships: a window nobody fixed, one call per candidate
departure, and a stay priced for the week that won. The network is the one thing
stubbed, which is the boundary a stub is for.
"""

from typing import Any

import pytest

from app_builder import assembled
from cora.domain.trace import ToolUse
from cora.engine.plugin_registry import load_plugin
from cora.engine.rounds import UNTRUSTED_NOTICE
from cora.plugins.travel import SCOPE
from cora.ports.chat_model import ModelReply
from cora.ports.plugin import ToolCall
from fakes import ScriptedChatModel

KEY = "a-key-this-deployment-was-given"
QUESTION = "One week in Lisbon somewhere in September, under 600 a head for the flight."
ANSWER = (
    "The week of 8 September is the cheapest — 318 to fly, and the Baixa room is 560 "
    "for the seven nights."
)

WINDOW = {
    "origin": "BER",
    "destination": "LIS",
    "window_start": "2026-09-01",
    "window_end": "2026-09-22",
    "nights": 7,
    "max_price": 600,
}
STAY = {
    "destination": "Lisbon",
    "check_in": "2026-09-08",
    "check_out": "2026-09-15",
    "max_price": 900,
}

FLIGHTS = {
    "2026-09-01": (690, 540),
    "2026-09-08": (318, 425),
    "2026-09-15": (612, 388),
}
"""What the service answers for each candidate departure. Three departures fit a
weekly stride inside the window, and the cheapest three fares are spread across two of
them — so a tool that kept the best of one departure would fail this."""

CHEAPEST = ("318", "388", "425")
DEARER = ("540", "612", "690")

STAYS = (("Alfama Rooms", 720), ("Baixa Suites", 560), ("Graca House", 940))


def _flights(departure: str) -> dict[str, Any]:
    return {
        "best_flights": [
            {
                "flights": [{"airline": "TAP Air Portugal", "flight_number": "TP 123"}],
                "price": fare,
                "departure_date": departure,
            }
            for fare in FLIGHTS[departure]
        ]
    }


def _properties() -> dict[str, Any]:
    return {
        "properties": [
            {
                "name": name,
                "hotel_class": "4-star hotel",
                "total_rate": {"lowest": f"€{rate}", "extracted_lowest": rate},
            }
            for name, rate in STAYS
        ]
    }


class Answer:
    """One reply, its own object — several departures are in flight at once, and a
    shared body would have them reading each other's."""

    def __init__(self, body: dict[str, Any]) -> None:
        self._body = body

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return self._body


class Service:
    """The search service, written out. It answers by engine, and keeps every query it
    was sent so the test can say what was actually asked of it."""

    def __init__(self) -> None:
        self.queries: list[dict[str, Any]] = []

    def get(self, url: str, *, params: dict[str, Any]) -> Answer:
        self.queries.append(dict(params))
        if params.get("engine") == "google_hotels":
            return Answer(_properties())
        return Answer(_flights(params["outbound_date"]))


@pytest.fixture
def service(monkeypatch: pytest.MonkeyPatch) -> Service:
    """Stubbed where the client is built, which is the one place the network is
    reached. The plugin, its registration and the whole turn are the real ones."""
    written = Service()
    monkeypatch.setattr(
        "cora.plugins.travel.trips._client", lambda: written, raising=True
    )
    return written


def test_a_week_nobody_fixed_comes_back_priced_and_within_the_budget(
    service: Service,
) -> None:
    """The criterion: a month range and a length rather than two dates, three flights
    and three stays priced against it, and the budget carried into the search itself
    rather than applied to what came back."""
    from cora.plugins.travel.trips import FLIGHTS_TOOL_NAME, HOTELS_TOOL_NAME

    model = ScriptedChatModel(
        [
            ModelReply(
                tool_calls=(
                    ToolCall(name=FLIGHTS_TOOL_NAME, arguments=WINDOW, call_id="f1"),
                )
            ),
            ModelReply(
                tool_calls=(
                    ToolCall(name=HOTELS_TOOL_NAME, arguments=STAY, call_id="h1"),
                )
            ),
            ModelReply(text=ANSWER),
        ]
    )
    app = assembled(
        chat_model=model,
        plugins=(load_plugin("cora.plugins.travel"),),
        scopes=(SCOPE,),
        plugin_settings={"cora.plugins.travel": {"serpapi_key": KEY}},
    )

    answered = app.agent.answer(QUESTION, "t1")

    departures = [
        query["outbound_date"] for query in service.queries if "outbound_date" in query
    ]
    assert departures == list(FLIGHTS), "a weekly stride tried every week in the window"
    assert len(service.queries) == len(FLIGHTS) + 1, "one stay, priced for the week"
    ceilings = {str(query.get("max_price")) for query in service.queries}
    assert ceilings == {"600", "900"}, (
        "the budget went into the search rather than filtering what came back"
    )

    assert answered.answer == ANSWER
    assert answered.citations == (), "a fetched price is nobody's passage to cite"

    told = [message for message in model.last_messages or () if message.role == "tool"]
    assert all(UNTRUSTED_NOTICE in message.content for message in told), (
        "what a service said reaches the model behind the label a passage carries"
    )

    used = [step for step in answered.trace if isinstance(step, ToolUse)]
    [flights] = [step for step in used if step.name == FLIGHTS_TOOL_NAME]
    assert all(fare in flights.detail for fare in CHEAPEST), "the three cheapest fares"
    assert not any(fare in flights.detail for fare in DEARER), "and only those three"
    assert "2026-09-08" in flights.detail, "each option says which week it belongs to"

    [stays] = [step for step in used if step.name == HOTELS_TOOL_NAME]
    assert all(name in stays.detail for name, _ in STAYS)
    assert not any(step.failed for step in used)


def test_the_key_reaches_the_service_and_nothing_else(service: Service) -> None:
    """A credential is the deployment's, not the conversation's: it goes out on the
    query and appears in neither what the model is given nor what the trace records."""
    from cora.plugins.travel.trips import FLIGHTS_TOOL_NAME

    model = ScriptedChatModel(
        [
            ModelReply(
                tool_calls=(
                    ToolCall(name=FLIGHTS_TOOL_NAME, arguments=WINDOW, call_id="f1"),
                )
            ),
            ModelReply(text=ANSWER),
        ]
    )
    app = assembled(
        chat_model=model,
        plugins=(load_plugin("cora.plugins.travel"),),
        scopes=(SCOPE,),
        plugin_settings={"cora.plugins.travel": {"serpapi_key": KEY}},
    )

    answered = app.agent.answer(QUESTION, "t2")

    assert all(query["api_key"] == KEY for query in service.queries)
    told = [message.content for message in model.last_messages or ()]
    assert not any(KEY in content for content in told)
    assert not any(KEY in str(step) for step in answered.trace)
