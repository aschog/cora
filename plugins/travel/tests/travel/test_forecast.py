import httpx
import pytest

from cora.plugins.travel.forecast import UNREACHABLE, UNREADABLE, Forecast, skies
from cora.ports.plugin import ToolRefusal

LISBON = {
    "results": [
        {"name": "Lisbon", "country": "Portugal", "latitude": 38.7, "longitude": -9.1}
    ]
}
THREE_DAYS = {
    "daily": {
        "time": ["2026-09-05", "2026-09-06", "2026-09-07"],
        "temperature_2m_max": [24.4, 25.1, 22.6],
        "temperature_2m_min": [17.2, 18.0, 16.6],
        "weather_code": [1, 61, 3],
    }
}


class Answered:
    """One written-out answer per call, in the order the tool makes them. Hand-written
    rather than a library's double: the network is the boundary, and what the tool needs
    of it is that an answer can fail and can be read."""

    def __init__(
        self,
        *answers: object,
        failing: Exception | None = None,
        status: Exception | None = None,
    ) -> None:
        self._answers = list(answers)
        self._failing = failing
        self._status = status
        self.asked: list[tuple[str, dict]] = []

    def get(self, url: str, *, params: dict) -> "Answered":
        self.asked.append((url, params))
        if self._failing is not None:
            raise self._failing
        self._body = self._answers.pop(0) if self._answers else None
        return self

    def raise_for_status(self) -> None:
        """The other door a failure comes through: the call connected and the service
        answered with a status. Both end in the same sentence, and only by going through
        this one is the `raise_for_status` in the tool exercised at all."""
        if self._status is not None:
            raise self._status

    def json(self) -> object:
        if isinstance(self._body, Exception):
            raise self._body
        return self._body


def test_a_forecast_is_fetched_for_a_named_place_and_written_as_one_line() -> None:
    """The place is resolved first, then its coordinates forecast, and what comes back
    is one line — the trace shows a plain payload under the same text the model reads,
    so a block here would be a paragraph where the reader wanted a line."""
    service = Answered(LISBON, THREE_DAYS)

    said = Forecast(service)("Lisbon", "2026-09-05", "2026-09-07")

    assert said == (
        "Lisbon, Portugal — 2026-09-05: 24/17°C, mainly clear; "
        "2026-09-06: 25/18°C, light rain; 2026-09-07: 23/17°C, overcast"
    )
    assert "\n" not in said
    [(_, located), (_, forecast)] = service.asked
    assert located["name"] == "Lisbon"
    assert (forecast["start_date"], forecast["end_date"]) == (
        "2026-09-05",
        "2026-09-07",
    )


def test_dates_nobody_asked_for_are_left_off_the_request() -> None:
    """Absent, the service answers with its own next few days — which is what "what
    will the weather be" means when no dates were named. Sending them empty would ask
    for a span beginning nowhere."""
    service = Answered(LISBON, THREE_DAYS)

    Forecast(service)("Lisbon")

    [_, (_, forecast)] = service.asked
    assert "start_date" not in forecast
    assert "end_date" not in forecast


def test_a_place_the_service_does_not_know_is_refused_rather_than_invented() -> None:
    """The refusal names the place, because the reader's next move is to try the town
    they actually meant."""
    service = Answered({"results": []})

    with pytest.raises(ToolRefusal) as refused:
        Forecast(service)("Atlantis")

    assert "Atlantis" in str(refused.value)


def _erroring() -> httpx.HTTPStatusError:
    return httpx.HTTPStatusError(
        "502",
        request=httpx.Request("GET", "https://example.invalid"),
        response=httpx.Response(502),
    )


@pytest.mark.parametrize(
    ("failing", "status"),
    [
        (httpx.ConnectError("no route"), None),
        (httpx.ReadTimeout("too slow"), None),
        (None, _erroring()),
    ],
    ids=["unreachable", "timed-out", "erroring"],
)
def test_a_service_that_does_not_answer_is_refused_in_one_friendly_line(
    failing: Exception | None, status: Exception | None
) -> None:
    """One sentence, and the same one however it failed: the reader is owed "no
    forecast, conversation intact", not the name of an exception class."""
    service = Answered(failing=failing, status=status)

    with pytest.raises(ToolRefusal) as refused:
        Forecast(service)("Lisbon")

    assert str(refused.value) == UNREACHABLE


def _daily(**rows: object) -> dict:
    return {"daily": {"time": ["2026-09-05", "2026-09-06"], **rows}}


@pytest.mark.parametrize(
    "answer",
    [
        ValueError("not json"),
        "a string where an object belongs",
        {"results": [{"name": "Lisbon"}]},
        {"results": [{"latitude": 38.7}]},
        {"results": ["Lisbon"]},
        {"results": {"name": "Lisbon"}},
        {"results": [{"name": "L", "latitude": "north", "longitude": "west"}]},
    ],
    ids=[
        "unparseable",
        "not-an-object",
        "no-latitude",
        "no-longitude",
        "a-string-for-a-place",
        "results-not-a-list",
        "a-point-that-is-not-a-point",
    ],
)
def test_a_place_the_service_answers_unreadably_is_refused(answer: object) -> None:
    """The leg that resolves the place is read as carefully as the one that forecasts
    it. A record with no point in it is not a place this can forecast, and the reader
    is owed the same sentence rather than the name of an exception class."""
    with pytest.raises(ToolRefusal) as refused:
        Forecast(Answered(answer))("Lisbon")

    assert str(refused.value) == UNREADABLE


@pytest.mark.parametrize(
    "answer",
    [
        ValueError("not json"),
        "a string where an object belongs",
        {"daily": {"time": []}},
        {"daily": {"time": ["2026-09-05"]}},
        {"nothing": "recognisable"},
        _daily(temperature_2m_max=[], temperature_2m_min=[], weather_code=[]),
        _daily(temperature_2m_max=[20], temperature_2m_min=[10], weather_code=[0]),
        _daily(
            temperature_2m_max=[20, None],
            temperature_2m_min=[10, 9],
            weather_code=[0, 0],
        ),
        _daily(
            temperature_2m_max=[20, "21"],
            temperature_2m_min=[10, 9],
            weather_code=[0, 0],
        ),
        _daily(temperature_2m_max="20", temperature_2m_min="10", weather_code="0"),
    ],
    ids=[
        "unparseable",
        "not-an-object",
        "no-days",
        "missing-measures",
        "wrong-shape",
        "no-readings-at-all",
        "fewer-readings-than-days",
        "a-day-the-service-left-out",
        "a-reading-that-is-not-a-number",
        "readings-that-are-not-lists",
    ],
)
def test_an_answer_the_tool_cannot_read_is_refused_rather_than_passed_on(
    answer: object,
) -> None:
    """A service whose shape moved must not become a forecast made of `None` — and must
    not become an empty one either. Every unreadable answer is the same sentence, and
    none of them reaches the model as weather: a day the service left out would
    otherwise be dropped in silence, which is a partial answer presented as a whole
    one."""
    with pytest.raises(ToolRefusal) as refused:
        Forecast(Answered(LISBON, answer))("Lisbon")

    assert str(refused.value) == UNREADABLE


@pytest.mark.integration
def test_the_real_service_answers_a_forecast_for_a_place_it_knows() -> None:
    """The shape the fakes above stand in for, pinned against the service itself: no
    credential, two addresses, and a daily block with the three measures in it. That
    the tool is declared as returning outside material is the plugin's own test."""
    said = Forecast()("Lisbon")

    assert "Lisbon" in said
    assert "°C" in said


def test_a_forecast_line_reads_back_as_a_sky_for_each_day() -> None:
    line = "Lisbon — 2026-09-07: 25/18°C, clear sky; 2026-09-08: 20/15°C, heavy rain"

    assert skies(line) == {"2026-09-07": "clear sky", "2026-09-08": "heavy rain"}


def test_a_line_that_is_not_a_forecast_reads_back_as_nothing() -> None:
    assert skies("could not reach the service") == {}
