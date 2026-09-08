import logging
from typing import Any

import httpx
import pytest

from cora.plugins.travel.trips import (
    CANDIDATES,
    FLIGHT_FIELDS,
    FLIGHTS_ASKED,
    HOTEL_FIELDS,
    SEARCH,
    UNREACHABLE,
    KeptOut,
    Search,
    _query,
    _schema,
    trip_tools,
)
from cora.ports.plugin import ToolRefusal

KEY = "a-key"
WEEK = {"window_start": "2026-09-08", "window_end": "2026-09-15", "nights": 7}
WINDOW = {"window_start": "2026-09-01", "window_end": "2026-09-22", "nights": 7}
ROUTE = {"origin": "BER", "destination": "LIS"}
STAY = {"destination": "Lisbon", "check_in": "2026-09-08", "check_out": "2026-09-15"}


class Answer:
    """One reply, its own object — so several departures in flight at once do not read
    each other's body."""

    def __init__(self, body: Any) -> None:
        self._body = body

    def raise_for_status(self) -> None:
        return None

    def json(self) -> Any:
        if isinstance(self._body, Exception):
            raise self._body
        return self._body


class Service:
    """The search service, written out: it keeps every query and answers by a rule the
    test hands it."""

    def __init__(self, reply: Any) -> None:
        self._reply = reply
        self.queries: list[dict[str, Any]] = []
        self.urls: list[str] = []

    def get(self, url: str, *, params: dict[str, Any]) -> Answer:
        self.queries.append(dict(params))
        self.urls.append(url)
        body = self._reply(params) if callable(self._reply) else self._reply
        if isinstance(body, httpx.HTTPError):
            raise body
        return Answer(body)


def flights(*prices: float) -> dict[str, Any]:
    return {
        "best_flights": [
            {"flights": [{"airline": "TAP Air Portugal"}], "price": price}
            for price in prices
        ]
    }


def stays(*rates: tuple[str, float]) -> dict[str, Any]:
    return {
        "properties": [
            {
                "name": name,
                "hotel_class": "4-star hotel",
                "total_rate": {"extracted_lowest": rate},
            }
            for name, rate in rates
        ]
    }


def searching(reply: Any) -> tuple[Search, Service]:
    service = Service(reply)
    return Search(KEY, service), service


def test_a_route_and_two_fixed_dates_come_back_as_the_service_priced_them() -> None:
    search, _ = searching(flights(240, 310))

    found = search.flights(**ROUTE, **WEEK)

    assert "EUR 240" in found
    assert "EUR 310" in found
    assert "TAP Air Portugal" in found


def test_only_the_cheapest_three_fares_come_back_and_in_that_order() -> None:
    """Three is what a person compares; the order is what makes the first one mean
    something."""
    search, _ = searching(flights(510, 240, 800, 310, 190))

    found = search.flights(**ROUTE, **WEEK)

    assert [fare for fare in ("190", "240", "310", "510", "800") if fare in found] == [
        "190",
        "240",
        "310",
    ]
    assert found.index("190") < found.index("240") < found.index("310")


def test_a_window_is_tried_one_departure_at_a_time() -> None:
    search, service = searching(flights(400))

    search.flights(**ROUTE, **WINDOW)

    assert [query["outbound_date"] for query in service.queries] == [
        "2026-09-01",
        "2026-09-08",
        "2026-09-15",
    ]
    assert [query["return_date"] for query in service.queries] == [
        "2026-09-08",
        "2026-09-15",
        "2026-09-22",
    ]


def test_a_sampling_too_close_to_afford_is_widened_rather_than_cut_short() -> None:
    """The range keeps its ends; what gives is how finely it is sampled, and the answer
    says how many departures were actually tried."""
    search, service = searching(flights(400))

    found = search.flights(
        **ROUTE,
        window_start="2026-09-01",
        window_end="2026-11-01",
        nights=7,
        stride_days=1,
    )

    assert len(service.queries) <= CANDIDATES
    assert service.queries[0]["outbound_date"] == "2026-09-01"
    assert f"tried {len(service.queries)} departures" in found


@pytest.mark.parametrize(
    ("fields", "given"), [(FLIGHT_FIELDS, ROUTE), (HOTEL_FIELDS, STAY)]
)
def test_every_searchable_field_reaches_the_schema_and_the_query_from_one_table(
    fields: tuple, given: dict[str, Any]
) -> None:
    """Said once and read twice, so a field somebody wants later is a row rather than
    an edit in two places that drift."""
    schema = _schema(fields)
    asked = {field.name: 3 if field.type == "integer" else "x" for field in fields}
    query = _query(fields, asked, KEY)

    assert set(schema["properties"]) == {field.name for field in fields}
    assert all(field.description for field in fields), "the model reads every one"
    assert {field.sends_as for field in fields if field.sends_as} <= set(query)
    assert set(schema["required"]) <= set(given) | {
        "window_start",
        "window_end",
        "nights",
    }


def test_a_service_that_cannot_be_reached_is_one_sentence() -> None:
    search, _ = searching(httpx.ConnectError("down"))

    with pytest.raises(ToolRefusal) as refused:
        search.stays(**STAY)

    assert str(refused.value) == UNREACHABLE


def test_the_key_is_kept_out_of_the_clients_own_request_log() -> None:
    """httpx logs the whole URL at INFO, and the key rides in the query string — so it
    would reach the operator's console the moment a deployment turns logging up."""
    logged = logging.LogRecord(
        "httpx",
        logging.INFO,
        "",
        0,
        'HTTP Request: %s %s "%s %d %s"',
        ("GET", httpx.URL(f"{SEARCH}?api_key={KEY}"), "HTTP/1.1", 200, "OK"),
        None,
    )

    assert KeptOut().filter(logged)
    assert KEY not in logged.getMessage()
    assert "api_key=REDACTED" in logged.getMessage(), (
        "the client logs its URL as its own object, not as a string"
    )
    assert "200" in logged.getMessage(), "the status stays a number its format needs"


# ── the search asks for the trip it was not told ──


def _asks(arguments: dict[str, Any]) -> Any:
    flying, _ = trip_tools(Search(KEY))
    assert flying.asks is not None
    return flying.asks(arguments)


def test_a_search_told_no_route_asks_for_the_trip_on_its_own_schema() -> None:
    """The fields the reader fills are the fields the service is sent, so the card and
    the search cannot drift."""
    card = _asks({})

    assert card is not None
    assert card.prompt == FLIGHTS_ASKED
    assert [field.name for field in card.fields] == [
        asked.name for asked in FLIGHT_FIELDS
    ]
    assert all(field.editable for field in card.fields)
