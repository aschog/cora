import logging
from typing import Any

import httpx
import pytest

from cora.plugins.travel.trips import (
    CANDIDATES,
    FLIGHT_FIELDS,
    FLIGHTS_ASKED,
    HOTEL_FIELDS,
    MOST,
    NOTHING_BOOKED,
    NOTHING_FLYING,
    NOWHERE_TO_STAY,
    REFUSED,
    SEARCH,
    SEARCH_IT,
    STAY_ASKED,
    UNREACHABLE,
    UNREADABLE,
    KeptOut,
    Search,
    _query,
    _schema,
    departures,
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


def test_every_fare_carries_its_price_its_currency_and_its_dates() -> None:
    search, _ = searching(flights(240))

    found = search.flights(**ROUTE, **WEEK, currency="GBP")

    assert "GBP 240" in found
    assert "2026-09-08 to 2026-09-15" in found


def test_a_service_that_found_nothing_flying_is_one_sentence() -> None:
    search, _ = searching({"best_flights": []})

    with pytest.raises(ToolRefusal) as refused:
        search.flights(**ROUTE, **WEEK)

    assert str(refused.value) == NOTHING_FLYING


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


def test_the_cheapest_three_are_taken_across_departures_not_within_one() -> None:
    """A tool that kept the best of each departure would pass a laxer test than this
    and answer a budget question wrongly."""
    fares = {"2026-09-01": (690, 540), "2026-09-08": (318, 425), "2026-09-15": (612,)}
    search, _ = searching(lambda query: flights(*fares[query["outbound_date"]]))

    found = search.flights(**ROUTE, **WINDOW)

    assert all(fare in found for fare in ("318", "425", "540"))
    assert not any(fare in found for fare in ("612", "690"))
    assert "2026-09-08 to 2026-09-15" in found, (
        "each fare says which week it belongs to"
    )


def test_departures_are_a_week_apart_unless_a_closer_sampling_is_asked_for() -> None:
    every_week, _ = departures({**WINDOW, "window_end": "2026-09-15"})
    every_day, stride = departures(
        {**WINDOW, "window_end": "2026-09-15", "stride_days": 1}
    )

    assert [day.isoformat() for day in every_week] == ["2026-09-01", "2026-09-08"]
    assert stride == 1
    assert len(every_day) == 8, "every day the trip could start on, inside the window"


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


def test_dates_already_fixed_fire_exactly_one_call() -> None:
    search, service = searching(flights(240))

    search.flights(**ROUTE, **WEEK)

    assert len(service.queries) == 1


def test_a_trip_that_does_not_fit_the_window_is_one_sentence() -> None:
    search, service = searching(flights(240))

    with pytest.raises(ToolRefusal) as refused:
        search.flights(
            **ROUTE, window_start="2026-09-01", window_end="2026-09-05", nights=7
        )

    assert "does not fit" in str(refused.value)
    assert service.queries == [], "nothing was asked of the service"


def test_the_cheapest_three_stays_come_back_priced_for_the_whole_stay() -> None:
    search, service = searching(
        stays(("Alfama", 720), ("Baixa", 560), ("Graca", 940), ("Chiado", 610))
    )

    found = search.stays(**STAY)

    assert all(name in found for name in ("Baixa", "Chiado", "Alfama"))
    assert "Graca" not in found
    assert "EUR 560 for the stay" in found
    assert len(service.queries) == 1, "somewhere to sleep is priced once, not per week"


def test_nowhere_to_stay_is_one_sentence() -> None:
    search, _ = searching({"properties": []})

    with pytest.raises(ToolRefusal) as refused:
        search.stays(**STAY)

    assert str(refused.value) == NOWHERE_TO_STAY


def test_a_price_ceiling_goes_into_the_search_rather_than_filtering_its_answer() -> (
    None
):
    search, service = searching(flights(240))

    search.flights(**ROUTE, **WEEK, max_price=600)

    assert service.queries[0]["max_price"] == "600"


def test_a_kind_of_place_ruled_out_goes_into_the_search_too() -> None:
    search, service = searching(stays(("Baixa", 560)))

    search.stays(**STAY, min_class=3)

    assert service.queries[0]["hotel_class"] == "3,4,5"


def test_what_the_service_returned_is_what_is_shown() -> None:
    """Nothing is dropped after the answer comes back: a filter cora applied afterwards
    is a filter the traveller cannot see, and a ceiling the service honoured is one
    they can."""
    search, _ = searching(flights(240, 900))

    found = search.flights(**ROUTE, **WEEK, max_price=600)

    assert "EUR 900" in found


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


def test_a_field_needing_shaping_is_written_the_way_its_row_says() -> None:
    """Stops the service counts from one and a person counts from none, and a lowest
    star rating is a list of the ratings above it."""
    assert _query(FLIGHT_FIELDS, {"stops": 0}, KEY)["stops"] == "1"
    assert _query(FLIGHT_FIELDS, {"stops": 1}, KEY)["stops"] == "2"
    assert _query(HOTEL_FIELDS, {"min_class": 4}, KEY)["hotel_class"] == "4,5"


def test_a_field_nobody_stated_is_left_out_rather_than_sent_empty() -> None:
    """An empty parameter is a filter to the service, and an absent one is not."""
    query = _query(HOTEL_FIELDS, STAY, KEY)

    assert "max_price" not in query
    assert "hotel_class" not in query


def test_a_service_that_cannot_be_reached_is_one_sentence() -> None:
    search, _ = searching(httpx.ConnectError("down"))

    with pytest.raises(ToolRefusal) as refused:
        search.stays(**STAY)

    assert str(refused.value) == UNREACHABLE


def test_an_answer_that_cannot_be_read_is_a_different_sentence() -> None:
    search, _ = searching(ValueError("not json"))

    with pytest.raises(ToolRefusal) as refused:
        search.stays(**STAY)

    assert str(refused.value) == UNREADABLE


def test_a_search_the_service_would_not_run_names_what_to_try_instead() -> None:
    """Its own words are never passed on: the query it quotes back carries the key."""
    search, _ = searching({"error": f"Unknown airport, key={KEY}"})

    with pytest.raises(ToolRefusal) as refused:
        search.flights(**ROUTE, **WEEK)

    assert str(refused.value) == REFUSED
    assert KEY not in str(refused.value)


def test_one_departure_the_service_choked_on_does_not_lose_the_others() -> None:
    def reply(query: dict[str, Any]) -> Any:
        if query["outbound_date"] == "2026-09-08":
            return httpx.ConnectError("down")
        return flights(400)

    search, _ = searching(reply)

    found = search.flights(**ROUTE, **WINDOW)

    assert "EUR 400" in found
    assert "tried 3 departures" in found


def test_every_departure_failing_is_the_failure_rather_than_an_empty_answer() -> None:
    search, _ = searching(httpx.ConnectError("down"))

    with pytest.raises(ToolRefusal) as refused:
        search.flights(**ROUTE, **WINDOW)

    assert str(refused.value) == UNREACHABLE


def test_both_searches_are_declared_as_returning_what_cora_did_not_write() -> None:
    flying, staying = trip_tools(KEY)

    assert [tool.untrusted for tool in (flying, staying)] == [True, True]
    assert not any(tool.effect for tool in (flying, staying))
    assert len(_schema(FLIGHT_FIELDS)["properties"]) == len(FLIGHT_FIELDS)
    assert MOST == 3


def test_where_the_searches_are_sent_is_the_deployments_to_say() -> None:
    """So a deployment with no key, no account and no network can still drive the real
    plugin against something that answers in the same shapes."""
    service = Service(flights(240))
    search = Search(KEY, service, url="http://127.0.0.1:8909/search")

    search.flights(**ROUTE, **WEEK)

    assert service.urls == ["http://127.0.0.1:8909/search"]


def test_the_searches_go_to_the_real_service_unless_told_otherwise() -> None:
    service = Service(flights(240))

    Search(KEY, service).flights(**ROUTE, **WEEK)

    assert service.urls == [SEARCH]


@pytest.mark.parametrize(
    "given",
    [
        {"nights": "seven"},
        {"stride_days": "weekly"},
        {"window_start": "September"},
        {"stops": "none"},
    ],
)
def test_an_argument_the_model_wrote_badly_is_a_sentence_not_a_crash(
    given: dict[str, Any],
) -> None:
    """The model is a trust boundary like any other: what it writes is checked, and
    what fails the check comes back as something the turn can answer around."""
    search, service = searching(flights(240))

    with pytest.raises(ToolRefusal):
        search.flights(**ROUTE, **{**WEEK, **given})

    assert service.queries == [], "nothing was asked of the service"


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
    flying, _ = trip_tools(KEY)
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


def test_the_card_says_which_of_its_fields_the_search_cannot_run_without() -> None:
    card = _asks({})

    required = {field.name for field in card.fields if field.required}
    assert required == {asked.name for asked in FLIGHT_FIELDS if asked.required}


def test_what_the_model_already_wrote_arrives_on_the_card_filled_in() -> None:
    card = _asks({"origin": "BER"})

    [origin] = [field for field in card.fields if field.name == "origin"]
    assert origin.value == "BER"


def test_a_day_is_asked_for_as_a_day_rather_than_as_a_string_to_get_right() -> None:
    """The format reaches the model in the schema and the reader as the control the card
    draws, so nobody has to type `YYYY-MM-DD` correctly."""
    card = _asks({})

    dated = {
        field.name for field in card.fields if field.schema.get("format") == "date"
    }
    assert dated == {"window_start", "window_end"}
    assert _schema(HOTEL_FIELDS)["properties"]["check_in"]["format"] == "date"


def test_the_submit_waits_for_the_card_and_the_way_out_does_not() -> None:
    search, not_now = _asks({}).actions

    assert (search.answer, search.needs_valid) == (SEARCH_IT, True)
    assert search.note == NOTHING_BOOKED
    assert (not_now.answer, not_now.needs_valid) == (None, False)


def test_a_search_told_everything_it_needs_asks_nothing() -> None:
    """The reader is asked when there is something to ask, not on every call."""
    assert _asks({**ROUTE, **WEEK}) is None


def test_the_stay_search_asks_on_its_own_schema_and_not_the_flights_one() -> None:
    _, staying = trip_tools(KEY)
    assert staying.asks is not None
    card = staying.asks({})

    assert card is not None
    assert card.prompt == STAY_ASKED
    assert [field.name for field in card.fields] == [
        asked.name for asked in HOTEL_FIELDS
    ]
