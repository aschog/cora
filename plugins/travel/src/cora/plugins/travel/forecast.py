"""The tool that asks a live service what the weather will do, and says what it said.

Open-Meteo, which needs no credential: a deployment that names this plugin can call it
with nothing configured, which is what keeps the story demonstrable. Two calls, because
the service resolves a place name and forecasts coordinates at separate addresses.
"""

import re
from dataclasses import dataclass, field
from typing import Any, Protocol

import httpx

from cora.ports.plugin import Tool, ToolRefusal

GEOCODING = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST = "https://api.open-meteo.com/v1/forecast"
MEASURES = "temperature_2m_max,temperature_2m_min,weather_code"
TIMEOUT = 10.0
A_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")

UNREACHABLE = (
    "I could not reach the forecast service just now, so I have no forecast to give "
    "you. Everything else in this conversation is unaffected."
)
UNREADABLE = (
    "The forecast service answered with something I could not read, so I have no "
    "forecast to give you."
)

CONDITIONS = {
    0: "clear",
    1: "mainly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "fog",
    48: "freezing fog",
    51: "light drizzle",
    53: "drizzle",
    55: "heavy drizzle",
    56: "freezing drizzle",
    57: "freezing drizzle",
    61: "light rain",
    63: "rain",
    65: "heavy rain",
    66: "freezing rain",
    67: "freezing rain",
    71: "light snow",
    73: "snow",
    75: "heavy snow",
    77: "snow grains",
    80: "light showers",
    81: "showers",
    82: "heavy showers",
    85: "snow showers",
    86: "heavy snow showers",
    95: "thunderstorms",
    96: "thunderstorms with hail",
    99: "thunderstorms with hail",
}
"""The WMO codes the service answers with, in the words a person would use. A code that
is not here is reported as unsettled rather than as a number: the model is writing prose
for someone planning a trip, and `code 73` is not a thing weather does."""


class Response(Protocol):
    """What the tool needs of an answer: that it can fail, and that it can be read."""

    def raise_for_status(self) -> Any: ...

    def json(self) -> Any: ...


class Fetcher(Protocol):
    """What the tool needs of a client, which is one call. Named as a shape rather than
    taken as `httpx.Client` so a test can hand over a written-out answer instead of a
    port, and so the timeout stays the caller's to set."""

    def get(self, url: str, *, params: dict[str, Any]) -> Response: ...


def _client() -> Fetcher:
    return httpx.Client(timeout=TIMEOUT)


@dataclass(frozen=True)
class Place:
    """Where the service says a place is: the name it knows it by, and its point."""

    name: str
    latitude: float
    longitude: float


@dataclass(frozen=True)
class Forecast:
    """One place resolved, then its forecast fetched and written as a single line."""

    fetch: Fetcher = field(default_factory=lambda: _client())
    """Looked up when one of these is built rather than when the class was declared, so
    the client is substitutable at the one place the network is reached. A test hands
    over a written-out answer; nothing else in the plugin knows the difference."""

    def __call__(
        self, place: str, start_date: str | None = None, end_date: str | None = None
    ) -> str:
        """The forecast for a place, on one line the model can read out.

        Each leg is read by something that answers with the shape the line needs, or
        refuses: nothing downstream of here handles a key that might be missing, so a
        service whose shape moved is one sentence rather than an exception class.

        Raises:
            ToolRefusal: The place is unknown to the service, the service could not be
                reached, or it answered with something this cannot read. Each is one
                sentence the turn can answer around.
        """
        located = _located(self._read(GEOCODING, {"name": place, "count": 1}))
        if located is None:
            raise ToolRefusal(
                f"The forecast service does not know a place called '{place}', so I "
                "have no forecast for it. A larger town nearby may work."
            )
        days = self._read(FORECAST, _asked(located, start_date, end_date))
        return f"{located.name} — {_days(days)}"

    def _read(self, url: str, params: dict[str, Any]) -> dict[str, Any]:
        try:
            answer = self.fetch.get(url, params=params)
            answer.raise_for_status()
        except httpx.HTTPError as unreachable:
            raise ToolRefusal(UNREACHABLE) from unreachable
        try:
            read = answer.json()
        except Exception as unreadable:
            raise ToolRefusal(UNREADABLE) from unreadable
        if not isinstance(read, dict):
            raise ToolRefusal(UNREADABLE)
        return read


def _asked(
    located: Place, start_date: str | None, end_date: str | None
) -> dict[str, Any]:
    asked: dict[str, Any] = {
        "latitude": located.latitude,
        "longitude": located.longitude,
        "daily": MEASURES,
        "timezone": "auto",
    }
    # Left out entirely rather than sent empty: absent, the service answers with its
    # own next few days, which is what "what will the weather be" means unasked.
    if start_date:
        asked["start_date"] = start_date
    if end_date:
        asked["end_date"] = end_date
    return asked


def _located(found: dict[str, Any]) -> Place | None:
    results = found.get("results")
    if results is None or results == []:
        return None
    if not isinstance(results, list) or not isinstance(results[0], dict):
        raise ToolRefusal(UNREADABLE)
    first = results[0]
    latitude, longitude = first.get("latitude"), first.get("longitude")
    if not isinstance(latitude, int | float) or not isinstance(longitude, int | float):
        raise ToolRefusal(UNREADABLE)
    named = [str(first.get(key, "")).strip() for key in ("name", "country")]
    return Place(
        name=", ".join(part for part in named if part),
        latitude=float(latitude),
        longitude=float(longitude),
    )


def _days(days: dict[str, Any]) -> str:
    daily = days.get("daily")
    if not isinstance(daily, dict):
        raise ToolRefusal(UNREADABLE)
    rows = [daily.get(key) for key in ("time", *MEASURES.split(","))]
    if not all(isinstance(row, list) for row in rows):
        raise ToolRefusal(UNREADABLE)
    dates, highs, lows, codes = rows
    if not dates or any(len(row) != len(dates) for row in rows):
        raise ToolRefusal(UNREADABLE)
    return "; ".join(
        f"{date}: {_degrees(high)}/{_degrees(low)}°C, {_sky(code)}"
        for date, high, low, code in zip(dates, highs, lows, codes, strict=True)
    )


def _degrees(reading: Any) -> str:
    if not isinstance(reading, int | float):
        raise ToolRefusal(UNREADABLE)
    return str(round(reading))


def _sky(code: Any) -> str:
    try:
        return CONDITIONS.get(int(code), "unsettled")
    except (TypeError, ValueError):
        return "unsettled"


FORECAST_TOOL_NAME = "fetch_forecast"
FORECAST_TOOL_DESCRIPTION = (
    "Fetch the weather forecast for a place from a live service. Call this whenever "
    "the answer turns on what the weather will actually do — the documents hold what "
    "somebody wrote down once, not what is coming. Dates are optional; without them "
    "the service answers with its next few days."
)
FORECAST_SCHEMA = {
    "type": "object",
    "properties": {
        "place": {
            "type": "string",
            "description": "The town or city to forecast, in the user's own words.",
        },
        "start_date": {
            "type": "string",
            "description": "First day to forecast, as YYYY-MM-DD.",
        },
        "end_date": {
            "type": "string",
            "description": "Last day to forecast, as YYYY-MM-DD.",
        },
    },
    "required": ["place"],
}


def forecast_tool() -> Tool:
    """The forecast as the model is offered it, declared as reaching outside cora.

    One definition, read twice: the plugin registers from it, and the researcher passes
    it to the loop it delegates. A second construction would be a second description of
    the same tool, and they would drift.
    """
    return Tool(
        name=FORECAST_TOOL_NAME,
        description=FORECAST_TOOL_DESCRIPTION,
        parameter_schema=FORECAST_SCHEMA,
        run=Forecast(),
        untrusted=True,
    )


def skies(line: str) -> dict[str, str]:
    """A forecast line read back as a word for the sky, by ISO date.

    Beside `_days`, which writes it: a reader of this shape belongs next to its writer,
    or the two drift. Anything unreadable is left out rather than guessed at, which
    makes a rule over it one that cannot fail rather than one that fails wrongly.
    """
    read: dict[str, str] = {}
    for part in line.split(";"):
        # The place heads the first day, so the date is what ends the left-hand side.
        named, _, rest = part.strip().partition(": ")
        day = A_DATE.search(named)
        sky = rest.rpartition(", ")[2].strip()
        if day is not None and sky:
            read[day.group()] = sky
    return read
