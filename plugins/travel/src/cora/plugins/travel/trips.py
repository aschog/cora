"""The tools that price a trip: what it costs to fly, and what it costs to stay.

SerpApi's Google Flights and Google Hotels engines, which need a key — so both tools
are offered only where the deployment set one. The engine wants a departure date, so a
window nobody has fixed is one call per candidate departure, fanned out here rather
than by the model.
"""

import datetime
import logging
import re
from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any

import httpx

from cora.domain.card import ActionOffered, Card, fields_of, missing_from
from cora.plugins.travel.forecast import Fetcher
from cora.ports.plugin import Tool, ToolRefusal

SEARCH = "https://serpapi.com/search"
SETTING = "serpapi_key"
ENDPOINT = "search_url"
"""What a deployment sets to send the searches somewhere else — a stand-in that answers
in the same shapes, so the plugin can be driven with no account and no network. A
setting rather than a flag: nothing branches on it, and the one address is still the
one address."""
TIMEOUT = 20.0
MOST = 3
"""How many options come back. Three is what a person compares without a spreadsheet."""
CANDIDATES = 8
"""The most departures one search may try. The service counts every one of them against
an hourly allowance, so a window sampled daily is widened rather than run."""
STRIDE = 7
WORKERS = 4
DEFAULTS = {"currency": "EUR"}

KEY_IN_A_URL = re.compile(r"(api_key=)[^&\s]+")
UNSPENT = "REDACTED"


class KeptOut(logging.Filter):
    """The key, taken back out of the client's own request log.

    httpx logs the whole URL at INFO and the service takes its credential in the query
    string, so a deployment that turns logging up would find the key in its console.
    A filter rather than a silenced logger: what is useful about that line stays.
    Numbers are left as they are, because the same line carries a status code its own
    format string needs as one; everything else is read as text, since the URL arrives
    as the client's own object rather than as a string.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        record.args = tuple(
            written
            if isinstance(written, int | float)
            else KEY_IN_A_URL.sub(rf"\1{UNSPENT}", str(written))
            for written in record.args or ()
        )
        return True


logging.getLogger("httpx").addFilter(KeptOut())
"""Installed once, when this module is first imported — which is when a deployment has
said it wants these tools, and before any client of theirs exists."""

UNREACHABLE = (
    "I could not reach the search service just now, so I have no prices to give you. "
    "Everything else in this conversation is unaffected."
)
UNREADABLE = (
    "The search service answered with something I could not read, so I have no prices "
    "to give you."
)
REFUSED = (
    "The search service would not run that search. The airport codes or the dates are "
    "the usual cause — a three-letter code and YYYY-MM-DD dates are what it wants."
)
TOO_SHORT = (
    "A {nights}-night trip does not fit between {start} and {end}, so there is nothing "
    "to price. Widen the window, or shorten the trip."
)
NOTHING_FLYING = "The service found no flights between those places in that window."
NOWHERE_TO_STAY = (
    "The service found nowhere to stay there on those dates within what you asked for."
)


@dataclass(frozen=True)
class Field:
    """One thing a search can be asked for, said once and read twice.

    The parameter schema the model is shown and the query the service is sent are both
    built from these, so a field somebody wants later is a row here rather than an edit
    in two places that drift.

    `sends_as` is the service's own name for it, and blank where the field is the
    tool's own — a window is planned here and never sent. `write` is how the value is
    written into the query, for the fields whose meaning is not their digits.
    """

    name: str
    type: str
    description: str
    sends_as: str = ""
    write: Callable[[Any], Any] = str
    required: bool = False


def _from(lowest: Any) -> str:
    return ",".join(str(star) for star in range(int(lowest), 6))


def _stops(most: Any) -> str:
    """The service counts stops from one, where a person counts them from none."""
    return str(int(most) + 1)


FLIGHT_FIELDS = (
    Field(
        "origin",
        "string",
        "Where the trip starts, as an airport or city code like BER.",
        "departure_id",
        required=True,
    ),
    Field(
        "destination",
        "string",
        "Where it goes, as an airport or city code like LIS.",
        "arrival_id",
        required=True,
    ),
    Field(
        "window_start",
        "string",
        "Earliest day the trip could start, as YYYY-MM-DD.",
        required=True,
    ),
    Field(
        "window_end",
        "string",
        "Latest day it could end, as YYYY-MM-DD. Where the dates are already fixed, "
        "this is the return date and only that one departure is tried.",
        required=True,
    ),
    Field("nights", "integer", "How many nights away.", required=True),
    Field(
        "stride_days",
        "integer",
        "How many days apart the departures tried are. Seven unless the traveller "
        "wants the window sampled more closely.",
    ),
    Field("max_price", "integer", "The most one fare may cost.", "max_price"),
    Field(
        "stops",
        "integer",
        "0 for non-stop only, 1 for one stop or fewer.",
        "stops",
        write=_stops,
    ),
    Field(
        "currency",
        "string",
        "Three-letter currency to price in. EUR unless the traveller asked otherwise.",
        "currency",
    ),
)

HOTEL_FIELDS = (
    Field(
        "destination",
        "string",
        "The place to stay, in the traveller's own words.",
        "q",
        required=True,
    ),
    Field(
        "check_in",
        "string",
        "First night, as YYYY-MM-DD.",
        "check_in_date",
        required=True,
    ),
    Field(
        "check_out",
        "string",
        "Morning of departure, as YYYY-MM-DD.",
        "check_out_date",
        required=True,
    ),
    Field("max_price", "integer", "The most the whole stay may cost.", "max_price"),
    Field(
        "min_class",
        "integer",
        "Lowest star rating to accept, 1 to 5. Three rules out hostels and guest "
        "houses.",
        "hotel_class",
        write=_from,
    ),
    Field(
        "currency",
        "string",
        "Three-letter currency to price in. EUR unless the traveller asked otherwise.",
        "currency",
    ),
)


def _schema(fields: Sequence[Field]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            asked.name: {"type": asked.type, "description": asked.description}
            for asked in fields
        },
        "required": [asked.name for asked in fields if asked.required],
        "additionalProperties": False,
    }


def _query(
    fields: Sequence[Field], given: Mapping[str, Any], key: str
) -> dict[str, Any]:
    """The query as the service reads it: the key, and the fields that go to it.

    A field the traveller did not state is left out rather than sent empty, because an
    empty parameter is a filter to the service and an absent one is not.

    Raises:
        ToolRefusal: A value the model wrote cannot be written into the query — a
            sentence rather than whatever `int` would have raised from inside a row.
    """
    query: dict[str, Any] = {"api_key": key}
    for asked in fields:
        value = given.get(asked.name)
        if not asked.sends_as or value is None:
            continue
        try:
            query[asked.sends_as] = asked.write(value)
        except (TypeError, ValueError) as unwritable:
            raise ToolRefusal(
                f"'{value}' is not something I can search on for {asked.name}."
            ) from unwritable
    return query


def _whole(given: Any, called: str) -> int:
    """One number the model wrote, read.

    Raises:
        ToolRefusal: It is not a whole number. The model is a trust boundary like any
            other, so what it writes is checked here rather than raised from `int`.
    """
    try:
        return int(given)
    except (TypeError, ValueError) as unreadable:
        raise ToolRefusal(
            f"'{given}' is not a whole number I can read for {called}."
        ) from unreadable


def _day(given: Any, called: str) -> datetime.date:
    """One date the model wrote, read.

    Raises:
        ToolRefusal: It is not a date, which is a sentence rather than a stack trace.
    """
    try:
        return datetime.date.fromisoformat(str(given))
    except ValueError as unreadable:
        raise ToolRefusal(
            f"'{given}' is not a date I can read for {called}; write it as YYYY-MM-DD."
        ) from unreadable


def departures(given: Mapping[str, Any]) -> tuple[list[datetime.date], int]:
    """Every departure this search will try, and how far apart they ended up.

    Fixed dates are the same shape with no slack in it — a window whose last possible
    departure is its first yields one day, so there is no second code path for them.

    Raises:
        ToolRefusal: The trip does not fit inside the window, or a date is unreadable.
    """
    start = _day(given["window_start"], "window_start")
    end = _day(given["window_end"], "window_end")
    nights = _whole(given["nights"], "nights")
    last = end - datetime.timedelta(days=nights)
    if last < start:
        raise ToolRefusal(
            TOO_SHORT.format(
                nights=nights, start=start.isoformat(), end=end.isoformat()
            )
        )
    stride = max(1, _whole(given.get("stride_days") or STRIDE, "stride_days"))
    span = (last - start).days
    if span // stride + 1 > CANDIDATES:
        stride = span // (CANDIDATES - 1) + 1
    days = [
        start + datetime.timedelta(days=step * stride)
        for step in range(span // stride + 1)
    ]
    return days, stride


@dataclass(frozen=True)
class Offer:
    """One thing that can be bought, and the one line it reads as."""

    price: float
    line: str


def _listed(head: str, offers: Sequence[Offer]) -> str:
    best = sorted(offers, key=lambda offer: offer.price)[:MOST]
    return f"{head} — " + "; ".join(offer.line for offer in best)


def _client() -> Fetcher:
    return httpx.Client(timeout=TIMEOUT)


@dataclass(frozen=True)
class Search:
    """One client, and the two searches that go out over it."""

    key: str
    fetch: Fetcher = field(default_factory=lambda: _client())
    url: str = SEARCH

    def flights(self, **given: Any) -> str:
        """The cheapest fares across every departure the window allows, on one line.

        Raises:
            ToolRefusal: The window holds no trip, every departure failed, or the
                service found nothing flying.
        """
        asked = {**DEFAULTS, **given}
        days, _ = departures(asked)
        nights = _whole(asked["nights"], "nights")
        currency = str(asked["currency"])
        base = _query(FLIGHT_FIELDS, asked, self.key) | {
            "engine": "google_flights",
            "type": "1",
        }
        with ThreadPoolExecutor(max_workers=WORKERS) as pool:
            found = list(
                pool.map(lambda day: self._fares(base, day, nights, currency), days)
            )
        refused = [answer for answer in found if isinstance(answer, ToolRefusal)]
        offers = [
            offer
            for answer in found
            if not isinstance(answer, ToolRefusal)
            for offer in answer
        ]
        if not offers:
            raise refused[0] if refused else ToolRefusal(NOTHING_FLYING)
        return _listed(f"tried {len(days)} departures", offers)

    def stays(self, **given: Any) -> str:
        """The cheapest places to stay for one set of dates, on one line.

        One call and no fan-out: the dates are settled by the time somewhere to sleep
        is worth pricing.

        Raises:
            ToolRefusal: The service could not be reached or read, or it found nowhere
                within what was asked for.
        """
        asked = {**DEFAULTS, **given}
        currency = str(asked["currency"])
        found = self._read(
            _query(HOTEL_FIELDS, asked, self.key) | {"engine": "google_hotels"}
        )
        listed = found.get("properties")
        if not isinstance(listed, list):
            raise ToolRefusal(UNREADABLE)
        offers = [
            offer for place in listed if (offer := _stay(place, currency)) is not None
        ]
        if not offers:
            raise ToolRefusal(NOWHERE_TO_STAY)
        return _listed(f"{min(len(offers), MOST)} of {len(offers)} stays", offers)

    def _fares(
        self, base: dict[str, Any], day: datetime.date, nights: int, currency: str
    ) -> list[Offer] | ToolRefusal:
        """One departure priced, or the refusal it earned.

        The refusal is carried back rather than raised, because one departure the
        service choked on must not lose the departures that worked.
        """
        back = day + datetime.timedelta(days=nights)
        try:
            found = self._read(
                base
                | {"outbound_date": day.isoformat(), "return_date": back.isoformat()}
            )
        except ToolRefusal as refusal:
            return refusal
        groups = [found.get(group) for group in ("best_flights", "other_flights")]
        if all(group is None for group in groups):
            return ToolRefusal(UNREADABLE)
        return [
            offer
            for group in groups
            if isinstance(group, list)
            for flight in group
            if (offer := _fare(flight, day, back, currency)) is not None
        ]

    def _read(self, query: dict[str, Any]) -> dict[str, Any]:
        """One call, read into a shape the rest of this does not have to guard.

        Raises:
            ToolRefusal: The service could not be reached, could not be read, or
                refused the search. Its own words are never passed on, because the
                query it is quoting carries the key.
        """
        try:
            answer = self.fetch.get(self.url, params=query)
            answer.raise_for_status()
        except httpx.HTTPError as unreachable:
            raise ToolRefusal(UNREACHABLE) from unreachable
        try:
            read = answer.json()
        except Exception as unreadable:
            raise ToolRefusal(UNREADABLE) from unreadable
        if not isinstance(read, dict):
            raise ToolRefusal(UNREADABLE)
        if read.get("error"):
            raise ToolRefusal(REFUSED)
        return read


def _fare(
    flight: Any, out: datetime.date, back: datetime.date, currency: str
) -> Offer | None:
    """One fare as a line, or nothing where the entry is not one.

    A malformed entry beside good ones is dropped rather than refused: the alternative
    is losing three usable fares to a fourth the service half-filled.
    """
    if not isinstance(flight, dict):
        return None
    price = flight.get("price")
    legs = flight.get("flights")
    if not isinstance(price, int | float) or not isinstance(legs, list) or not legs:
        return None
    first = legs[0] if isinstance(legs[0], dict) else {}
    airline = str(first.get("airline", "")).strip() or "unnamed carrier"
    stops = len(legs) - 1
    changes = "non-stop" if stops == 0 else f"{stops} stop" + ("s" if stops > 1 else "")
    return Offer(
        price=float(price),
        line=(
            f"{out.isoformat()} to {back.isoformat()}: {airline}, {changes}, "
            f"{currency} {price:g}"
        ),
    )


def _stay(place: Any, currency: str) -> Offer | None:
    """One place to stay as a line, or nothing where the entry is not one."""
    if not isinstance(place, dict):
        return None
    rate = place.get("total_rate")
    price = rate.get("extracted_lowest") if isinstance(rate, dict) else None
    name = str(place.get("name", "")).strip()
    if not isinstance(price, int | float) or not name:
        return None
    kind = str(place.get("hotel_class", "")).strip()
    return Offer(
        price=float(price),
        line=f"{name}{f', {kind}' if kind else ''}, {currency} {price:g} for the stay",
    )


FLIGHTS_TOOL_NAME = "search_flights"
FLIGHTS_TOOL_DESCRIPTION = (
    "Search live flight prices and return the cheapest few. Give a window rather than "
    "two dates when the traveller has not fixed them — an earliest start, a latest "
    "return and a number of nights — and several departures across it are tried. "
    "Where the dates are fixed, set the window to exactly those dates."
)
HOTELS_TOOL_NAME = "search_hotels"
HOTELS_TOOL_DESCRIPTION = (
    "Search live accommodation prices for one set of dates and return the cheapest "
    "few. Call it once the dates are settled. A budget or a minimum star rating is "
    "applied by the search itself, so what comes back is already within them."
)


FLIGHTS_ASKED = "Give me the trip and I'll price the flights."
STAY_ASKED = "Give me the stay and I'll price it."
SEARCH_IT = "Search"
NOT_NOW = "Not now"
NOTHING_BOOKED = "Nothing is booked without a second confirmation."
SEARCHING = "You gave me the trip."
NOT_SEARCHING = "You did not give me the trip, so nothing was searched."


def _asking(
    fields: Sequence[Field], prompt: str
) -> Callable[[dict[str, Any]], Card | None]:
    """The card this search puts up when the model could not say what to search for.

    Built from the search's own schema, so the fields the reader fills are the fields
    the service is sent and the two cannot drift. A call that already names everything
    required raises nothing: the reader is asked when there is something to ask.
    """
    schema = _schema(fields)

    def asks(arguments: dict[str, Any]) -> Card | None:
        if not missing_from(schema, arguments):
            return None
        return Card(
            prompt=prompt,
            fields=fields_of(schema, arguments),
            actions=(
                ActionOffered(
                    label=SEARCH_IT,
                    answer=SEARCH_IT,
                    note=NOTHING_BOOKED,
                    needs_valid=True,
                    settled=SEARCHING,
                ),
                ActionOffered(label=NOT_NOW, answer=None, settled=NOT_SEARCHING),
            ),
        )

    return asks


def trip_tools(key: str, url: str = SEARCH) -> tuple[Tool, ...]:
    """Both searches over one client, declared as returning what cora did not write.

    Args:
        url: Where the searches go, for a deployment standing something else in front
            of them.
    """
    search = Search(key, url=url)
    return (
        Tool(
            name=FLIGHTS_TOOL_NAME,
            description=FLIGHTS_TOOL_DESCRIPTION,
            parameter_schema=_schema(FLIGHT_FIELDS),
            run=search.flights,
            untrusted=True,
            asks=_asking(FLIGHT_FIELDS, FLIGHTS_ASKED),
        ),
        Tool(
            name=HOTELS_TOOL_NAME,
            description=HOTELS_TOOL_DESCRIPTION,
            parameter_schema=_schema(HOTEL_FIELDS),
            run=search.stays,
            untrusted=True,
            asks=_asking(HOTEL_FIELDS, STAY_ASKED),
        ),
    )
