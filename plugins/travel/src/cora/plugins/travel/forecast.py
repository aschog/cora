"""The tool that asks a live service what the weather will do, and says what it said.

Open-Meteo, which needs no credential: a deployment that names this plugin can call it
with nothing configured, which is what keeps the story demonstrable. Two calls, because
the service resolves a place name and forecasts coordinates at separate addresses.
"""

from dataclasses import dataclass, field
from typing import Any, Protocol

import httpx

from cora.ports.plugin import ToolRefusal

GEOCODING = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST = "https://api.open-meteo.com/v1/forecast"
MEASURES = "temperature_2m_max,temperature_2m_min,weather_code"
TIMEOUT = 10.0

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

        Raises:
            ToolRefusal: The place is unknown to the service, the service could not be
                reached, or it answered with something this cannot read. Each is one
                sentence the turn can answer around.
        """
        found = self._read(GEOCODING, {"name": place, "count": 1})
        located = (found.get("results") or [None])[0]
        if located is None:
            raise ToolRefusal(
                f"The forecast service does not know a place called '{place}', so I "
                "have no forecast for it. A larger town nearby may work."
            )
        days = self._read(FORECAST, self._where(located, start_date, end_date))
        return f"{_named(located)} — {_days(days)}"

    def _where(
        self, located: dict[str, Any], start_date: str | None, end_date: str | None
    ) -> dict[str, Any]:
        asked = {
            "latitude": located["latitude"],
            "longitude": located["longitude"],
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


def _named(located: dict[str, Any]) -> str:
    """The place as the service knows it, so the reader can see it was understood."""
    named = [
        str(located.get("name", "")).strip(),
        str(located.get("country", "")).strip(),
    ]
    return ", ".join(part for part in named if part)


def _days(days: dict[str, Any]) -> str:
    """Every day on one line: the date, a high, a low and a word for the sky.

    One line because a tool that hands back plain prose is shown in the trace under the
    same text the model is given, so a block would be a paragraph where the reader
    wanted a line.

    Raises:
        ToolRefusal: The answer is not shaped like a forecast.
    """
    daily = days.get("daily")
    if not isinstance(daily, dict):
        raise ToolRefusal(UNREADABLE)
    try:
        dates = list(daily["time"])
        highs = list(daily["temperature_2m_max"])
        lows = list(daily["temperature_2m_min"])
        codes = list(daily["weather_code"])
    except (KeyError, TypeError) as unreadable:
        raise ToolRefusal(UNREADABLE) from unreadable
    if not dates:
        raise ToolRefusal(UNREADABLE)
    return "; ".join(
        f"{date}: {round(high)}/{round(low)}°C, {_sky(code)}"
        for date, high, low, code in zip(dates, highs, lows, codes, strict=False)
    )


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
