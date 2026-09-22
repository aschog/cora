import httpx
import pytest

from cora.plugins.travel.forecast import UNREACHABLE, Forecast, skies
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
        if self._status is not None:
            raise self._status

    def json(self) -> object:
        if isinstance(self._body, Exception):
            raise self._body
        return self._body


def test_a_forecast_is_fetched_for_a_named_place_and_written_as_one_line() -> None:
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


def test_a_place_the_service_does_not_know_is_refused_rather_than_invented() -> None:
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
    service = Answered(failing=failing, status=status)

    with pytest.raises(ToolRefusal) as refused:
        Forecast(service)("Lisbon")

    assert str(refused.value) == UNREACHABLE


@pytest.mark.integration
def test_the_real_service_answers_a_forecast_for_a_place_it_knows() -> None:
    said = Forecast()("Lisbon")

    assert "Lisbon" in said
    assert "°C" in said


def test_a_forecast_line_reads_back_as_a_sky_for_each_day() -> None:
    line = "Lisbon — 2026-09-07: 25/18°C, clear sky; 2026-09-08: 20/15°C, heavy rain"

    assert skies(line) == {"2026-09-07": "clear sky", "2026-09-08": "heavy rain"}
