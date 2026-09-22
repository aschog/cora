import datetime
from typing import Any

import httpx
import pytest

from cora.plugins.travel.planner import (
    DAY_SHAPE,
    NO_DAYS,
    PASSES,
    UNPRICED,
    UNPRICED_FAILED,
    Planner,
)
from cora.plugins.travel.trips import Search
from cora.ports.plugin import ToolRefusal

KEY = "a-key"
TRIP: dict[str, Any] = {
    "origin": "BER",
    "destination": "Lisbon",
    "arrival": "LIS",
    "window_start": "2026-09-01",
    "window_end": "2026-09-22",
    "nights": 3,
    "budget": 800,
}
SHAPE: dict[str, Any] = {
    "days": [
        {"on": "2026-09-01", "doing": ["Alfama"], "outdoor": False},
        {"on": "2026-09-02", "doing": ["Belem"], "outdoor": True},
        {"on": "2026-09-03", "doing": ["Market"], "outdoor": False},
    ]
}


class Answer:
    def __init__(self, body: Any) -> None:
        self._body = body

    def raise_for_status(self) -> None:
        return None

    def json(self) -> Any:
        return self._body


class Refusing:
    def __init__(self) -> None:
        self.queries: list[dict[str, Any]] = []

    def get(self, url: str, *, params: dict[str, Any]) -> Answer:
        self.queries.append(dict(params))
        if params.get("engine") == "google_flights":
            raise httpx.ConnectError("down")
        return Answer({"properties": []})


class Service:
    def __init__(
        self,
        fares: dict[str, float] | None = None,
        stay: float = 240.0,
        stays: dict[str, float] | None = None,
    ):
        self.fares = fares or {}
        self.stay = stay
        self.stays = stays or {}
        self.queries: list[dict[str, Any]] = []

    def get(self, url: str, *, params: dict[str, Any]) -> Answer:
        self.queries.append(dict(params))
        if params.get("engine") == "google_flights":
            for end in ("departure_id", "arrival_id"):
                assert len(params[end]) == 3 and params[end].isupper(), (
                    f"the flights engine reads a code, and was sent {params[end]!r}"
                )
            price = self.fares.get(params["outbound_date"], 300.0)
            return Answer(
                {"best_flights": [{"flights": [{"airline": "TAP"}], "price": price}]}
            )
        rate = self.stays.get(params.get("check_in_date", ""), self.stay)
        return Answer(
            {
                "properties": [
                    {
                        "name": "Hotel Baixa",
                        "hotel_class": "3-star hotel",
                        "total_rate": {"extracted_lowest": rate},
                    }
                ]
            }
        )


class Cora:
    def __init__(self, *shapes: Any) -> None:
        self._shapes = list(shapes) or [SHAPE]
        self.tasks: list[str] = []
        self.shapes: list[Any] = []
        self.shown: list[tuple[str, str, bool]] = []
        self.kept: dict[str, str] = {}

    def delegate(
        self, task: str, tools: Any = (), rounds: int = 3, *, shape: Any = None
    ) -> Any:
        self.tasks.append(task)
        self.shapes.append(shape)
        answered = self._shapes[min(len(self.tasks) - 1, len(self._shapes) - 1)]
        if isinstance(answered, ToolRefusal):
            raise answered
        return answered

    def show(self, did: str, detail: str = "", failed: bool = False) -> None:
        self.shown.append((did, detail, failed))

    @property
    def state(self) -> "Cora":
        return self

    def read(self, name: str) -> str | None:
        return self.kept.get(name)

    def keep(self, name: str, value: str | None) -> None:
        if value is None:
            self.kept.pop(name, None)
        else:
            self.kept[name] = value


def _planner(cora: Cora, service: Any = None, **over: Any) -> Planner:
    search = None if service is None else Search(KEY, service)
    return Planner(cora=cora, search=search, **over)  # ty: ignore[invalid-argument-type]


def test_one_call_comes_back_with_a_dated_priced_plan() -> None:
    cora = Cora()

    read = _planner(cora, Service()).plan(**TRIP)

    assert "BER to Lisbon" in read
    assert "total: EUR 540" in read
    assert "2026-09-01: Alfama" in read


def test_the_cheapest_departure_of_the_window_is_the_one_planned() -> None:
    cora = Cora()
    service = Service(fares={"2026-09-08": 100.0})

    read = _planner(cora, service).plan(**TRIP)

    assert "2026-09-08 to 2026-09-11" in read
    assert "total: EUR 340" in read


def test_a_plan_over_budget_is_revised_and_searched_again() -> None:
    cora = Cora()
    service = Service(stay=900.0)

    _planner(cora, service).plan(**TRIP)

    assert len(cora.tasks) == PASSES + 1


def test_no_constraint_the_traveller_gave_is_relaxed_to_make_a_plan_hold() -> None:
    cora = Cora()

    read = _planner(cora, Service(stay=900.0)).plan(**TRIP)

    assert "800" in read
    assert "the plan holds" not in read


def test_a_revision_starts_from_the_plan_that_was_kept() -> None:
    cora = Cora()
    planner = _planner(cora, Service())
    planner.plan(**TRIP)

    read = planner.revise("somewhere cheaper to stay", budget=600)

    assert "BER to Lisbon" in read


def test_the_planning_is_shown_on_the_trace() -> None:
    cora = Cora()

    _planner(cora, Service()).plan(**TRIP)

    assert any("priced" in did for did, _, _ in cora.shown)


def test_the_flight_is_searched_by_code_and_the_stay_by_the_place_in_words() -> None:
    cora = Cora()
    service = Service()

    _planner(cora, service).plan(**TRIP)

    flights = [q for q in service.queries if q.get("engine") == "google_flights"]
    hotels = [q for q in service.queries if q.get("engine") == "google_hotels"]
    assert {q["arrival_id"] for q in flights} == {"LIS"}
    assert {q["q"] for q in hotels} == {"Lisbon"}
    assert "Lisbon" in cora.tasks[0]


def test_a_revision_prices_the_flights_the_kept_plan_was_priced_by() -> None:
    cora = Cora()
    planner = _planner(cora, Service())
    planner.plan(**TRIP)

    read = planner.revise("somewhere cheaper to stay")

    assert "total: EUR" in read


def test_prices_that_could_not_be_had_are_not_reported_as_none_configured() -> None:
    cora = Cora()

    failed = _planner(cora, Refusing()).plan(**TRIP)
    absent = _planner(cora).plan(**TRIP)

    assert UNPRICED_FAILED in failed
    assert UNPRICED in absent


def test_the_days_are_asked_for_as_a_shape_and_read_as_a_value() -> None:
    cora = Cora()

    read = _planner(cora, Service()).plan(**TRIP)

    assert cora.shapes == [DAY_SHAPE]
    assert DAY_SHAPE["required"] == ["days"], "an empty answer must not satisfy it"
    assert "Alfama" in read


def test_days_that_came_back_empty_are_shown_and_revised() -> None:
    cora = Cora({"days": []})

    _planner(cora, Service()).plan(**TRIP)

    assert any(did == NO_DAYS and failed for did, _, failed in cora.shown)
    assert len(cora.tasks) == PASSES + 1, "the passes were spent revising"


def test_a_day_whose_date_cannot_be_read_is_dropped() -> None:
    cora = Cora(
        {
            "days": [
                {"on": "the first", "doing": ["Alfama"]},
                {"on": "2026-09-02", "doing": ["Belem"]},
            ]
        }
    )

    # No search service, so the days keep the dates the model gave them.
    read = _planner(cora).plan(**TRIP)

    assert "2026-09-02: Belem" in read
    assert "the first" not in read


def test_a_loop_that_will_not_answer_in_the_shape_fails_the_call() -> None:
    cora = Cora(ToolRefusal("the sub-agent wrote prose"))

    with pytest.raises(ToolRefusal):
        _planner(cora, Service()).plan(**TRIP)

    assert len(cora.tasks) == 1, "it is not asked twice for what it will not answer"


def test_a_datetime_free_planner_needs_no_clock() -> None:
    cora = Cora()

    read = _planner(cora, Service()).plan(**TRIP)

    assert datetime.date.today().isoformat() not in read
