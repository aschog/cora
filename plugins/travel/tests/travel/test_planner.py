import datetime
import json
from typing import Any

import pytest

from cora.engine import keeping
from cora.plugins.travel.plan import plan_from
from cora.plugins.travel.planner import (
    KEPT,
    PASSES,
    Planner,
    planning_tools,
)
from cora.plugins.travel.trips import Search
from cora.ports.plugin import ToolRefusal

KEY = "a-key"
TRIP: dict[str, Any] = {
    "origin": "BER",
    "destination": "Lisbon",
    "window_start": "2026-09-01",
    "window_end": "2026-09-22",
    "nights": 3,
    "budget": 800,
}
SHAPE = json.dumps(
    [
        {"on": "2026-09-01", "doing": ["Alfama"], "outdoor": False},
        {"on": "2026-09-02", "doing": ["Belem"], "outdoor": True},
        {"on": "2026-09-03", "doing": ["Market"], "outdoor": False},
    ]
)


class Answer:
    def __init__(self, body: Any) -> None:
        self._body = body

    def raise_for_status(self) -> None:
        return None

    def json(self) -> Any:
        return self._body


class Service:
    """The search service written out, pricing a fare by its departure so a window has
    a cheapest week in it."""

    def __init__(self, fares: dict[str, float] | None = None, stay: float = 240.0):
        self.fares = fares or {}
        self.stay = stay
        self.queries: list[dict[str, Any]] = []

    def get(self, url: str, *, params: dict[str, Any]) -> Answer:
        self.queries.append(dict(params))
        if params.get("engine") == "google_flights":
            price = self.fares.get(params["outbound_date"], 300.0)
            return Answer(
                {"best_flights": [{"flights": [{"airline": "TAP"}], "price": price}]}
            )
        return Answer(
            {
                "properties": [
                    {
                        "name": "Hotel Baixa",
                        "hotel_class": "3-star hotel",
                        "total_rate": {"extracted_lowest": self.stay},
                    }
                ]
            }
        )


class Cora:
    """The host the planner is closed over, written out: it answers the delegated call
    with whatever shape the test scripts, and keeps what the planner keeps."""

    def __init__(self, *shapes: str) -> None:
        self._shapes = list(shapes) or [SHAPE]
        self.tasks: list[str] = []
        self.shown: list[tuple[str, bool]] = []
        self.kept: dict[str, str] = {}

    def delegate(self, task: str, tools: Any = (), rounds: int = 3) -> str:
        self.tasks.append(task)
        return self._shapes[min(len(self.tasks) - 1, len(self._shapes) - 1)]

    def show(self, did: str, detail: str = "", failed: bool = False) -> None:
        self.shown.append((did, failed))

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


def _planner(cora: Cora, service: Service | None = None, **over: Any) -> Planner:
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


def test_every_departure_of_the_window_is_priced() -> None:
    cora = Cora()
    service = Service()

    _planner(cora, service).plan(**TRIP)

    flights = [q for q in service.queries if q.get("engine") == "google_flights"]
    assert len({q["outbound_date"] for q in flights}) > 1


def test_only_the_cheapest_few_departures_are_paired_with_a_stay() -> None:
    cora = Cora()
    service = Service()

    _planner(cora, service).plan(**TRIP)

    stays = [q for q in service.queries if q.get("engine") == "google_hotels"]
    assert len(stays) <= 3


def test_a_plan_that_holds_stops_the_loop_on_its_first_pass() -> None:
    cora = Cora()

    _planner(cora, Service()).plan(**TRIP)

    assert len(cora.tasks) == 1


def test_a_plan_over_budget_is_revised_and_searched_again() -> None:
    cora = Cora()
    service = Service(stay=900.0)

    _planner(cora, service).plan(**TRIP)

    assert len(cora.tasks) == PASSES + 1


def test_a_plan_that_cannot_be_made_to_hold_is_offered_with_what_it_failed() -> None:
    cora = Cora()

    read = _planner(cora, Service(stay=900.0)).plan(**TRIP)

    assert "could not be made to satisfy" in read
    assert "over the 800 budget" in read


def test_no_constraint_the_traveller_gave_is_relaxed_to_make_a_plan_hold() -> None:
    cora = Cora()

    read = _planner(cora, Service(stay=900.0)).plan(**TRIP)

    assert "800" in read
    assert "the plan holds" not in read


def test_a_model_that_says_it_is_finished_does_not_end_a_failing_loop() -> None:
    """The terminal condition is a check passing, never anything the model wrote."""
    cora = Cora("Done! The plan is perfect and needs no further work.")

    read = _planner(cora, Service()).plan(**TRIP)

    assert "could not be made to satisfy" in read
    assert len(cora.tasks) == PASSES + 1


def test_an_empty_day_is_caught_and_the_shape_asked_for_again() -> None:
    cora = Cora(json.dumps([{"on": "2026-09-01", "doing": []}]))

    _planner(cora, Service()).plan(**TRIP)

    assert "failed these checks" in cora.tasks[-1]


def test_a_candidate_the_forecast_rules_out_is_passed_over_for_one_that_holds() -> None:
    cora = Cora()
    wet = "Lisbon — 2026-09-02: 18/12°C, heavy rain"

    read = _planner(cora, Service(), weather=lambda place: wet).plan(**TRIP)

    assert "2026-09-01 to" not in read
    assert "the plan holds" in read


def test_an_outdoor_day_the_forecast_rules_out_is_named_when_none_holds() -> None:
    cora = Cora()
    wet = "; ".join(f"2026-09-{day:02d}: 18/12°C, heavy rain" for day in range(1, 23))

    read = _planner(cora, Service(), weather=lambda place: wet).plan(**TRIP)

    assert "rules out what is planned outdoors" in read


def test_a_forecast_that_cannot_be_had_costs_the_plan_one_rule_and_not_the_trip() -> (
    None
):
    def down(place: str) -> str:
        raise ToolRefusal("the forecast service is down")

    read = _planner(Cora(), Service(), weather=down).plan(**TRIP)

    assert "the plan holds" in read


def test_a_search_that_cannot_be_reached_costs_the_prices_and_not_the_turn() -> None:
    class Down(Service):
        def get(self, url: str, *, params: dict[str, Any]) -> Answer:
            raise __import__("httpx").ConnectError("down")

    read = _planner(Cora(), Down()).plan(**TRIP)

    assert "no prices" in read
    assert "2026-09-01: Alfama" in read


def test_with_no_search_service_the_days_are_planned_and_said_to_be_unpriced() -> None:
    read = _planner(Cora(), None).plan(**TRIP)

    assert "no prices" in read
    assert "2026-09-01: Alfama" in read


def test_the_plan_is_kept_for_the_conversation_it_was_planned_in() -> None:
    cora = Cora()

    _planner(cora, Service()).plan(**TRIP)

    assert plan_from(json.loads(cora.kept[KEPT])).destination == "Lisbon"


def test_a_revision_starts_from_the_plan_that_was_kept() -> None:
    cora = Cora()
    planner = _planner(cora, Service())
    planner.plan(**TRIP)

    read = planner.revise("somewhere cheaper to stay", budget=600)

    assert "BER to Lisbon" in read


def test_a_revision_with_nothing_kept_refuses_in_a_sentence() -> None:
    with pytest.raises(ToolRefusal, match="nothing to revise"):
        _planner(Cora(), Service()).revise("cheaper")


def test_a_revision_that_cannot_hold_says_which_part_failed() -> None:
    cora = Cora()
    planner = _planner(cora, Service())
    planner.plan(**TRIP)

    read = planner.revise("much cheaper", budget=100)

    assert "over the 100 budget" in read


def test_the_planning_is_shown_on_the_trace() -> None:
    cora = Cora()

    _planner(cora, Service()).plan(**TRIP)

    assert any("priced" in did for did, _ in cora.shown)


def test_a_pass_that_found_nothing_that_holds_is_shown_as_failed() -> None:
    cora = Cora()

    _planner(cora, Service(stay=900.0)).plan(**TRIP)

    assert any(failed for _, failed in cora.shown)


def test_an_unreadable_date_refuses_rather_than_planning_something_else() -> None:
    with pytest.raises(ToolRefusal, match="not a date"):
        _planner(Cora(), Service()).plan(**(TRIP | {"window_start": "next tuesday"}))


def test_both_planning_tools_say_what_they_return_is_not_cora_s_own_words() -> None:
    tools = planning_tools(Cora(), None)  # ty: ignore[invalid-argument-type]

    assert [tool.untrusted for tool in tools] == [True, True]


def test_neither_planning_tool_declares_an_effect_or_stops_the_turn() -> None:
    tools = planning_tools(Cora(), None)  # ty: ignore[invalid-argument-type]

    assert not any(tool.effect or tool.asks for tool in tools)


def test_the_planner_keeps_under_the_host_it_was_handed() -> None:
    """The keeping is the host's, so a real host namespaces it by plugin."""
    cora = Cora()

    with keeping.bound({}):
        _planner(cora, Service()).plan(**TRIP)

    assert KEPT in cora.kept


def test_a_day_shape_that_is_not_json_leaves_the_days_empty_and_is_revised() -> None:
    cora = Cora("I could not work that out.")

    read = _planner(cora, Service()).plan(**TRIP)

    assert "nothing is planned" in read


def test_the_nights_planned_are_the_nights_asked_for() -> None:
    cora = Cora()

    read = _planner(cora, Service()).plan(**TRIP)

    assert "3 nights" in read


def test_the_stay_covers_every_night_of_the_fare_it_was_paired_with() -> None:
    cora = Cora()
    service = Service(fares={"2026-09-08": 100.0})

    _planner(cora, service).plan(**TRIP)

    [stay] = [q for q in service.queries if q.get("engine") == "google_hotels"][:1]
    assert stay["check_in_date"] == "2026-09-08"
    assert stay["check_out_date"] == "2026-09-11"


def test_the_budget_goes_into_the_search_rather_than_filtering_afterwards() -> None:
    cora = Cora()
    service = Service()

    _planner(cora, service).plan(**TRIP)

    [fares] = [q for q in service.queries if q.get("engine") == "google_flights"][:1]
    assert fares["max_price"] == "800"


def test_a_trip_with_no_budget_is_not_priced_against_one_of_zero() -> None:
    cora = Cora()
    service = Service(stay=900.0)

    read = _planner(cora, service).plan(
        **{k: v for k, v in TRIP.items() if k != "budget"}
    )

    assert "the plan holds" in read


def test_the_days_are_moved_onto_the_week_that_was_actually_priced() -> None:
    cora = Cora()
    service = Service(fares={"2026-09-08": 100.0})

    read = _planner(cora, service).plan(**TRIP)

    assert "2026-09-08: Alfama" in read


def test_a_date_that_is_not_a_date_in_the_shape_is_dropped_rather_than_guessed() -> (
    None
):
    cora = Cora(json.dumps([{"on": "soon", "doing": ["Alfama"]}]))

    read = _planner(cora, Service()).plan(**TRIP)

    assert "nothing is planned" in read


def test_the_window_is_what_the_search_is_given() -> None:
    cora = Cora()
    service = Service()

    _planner(cora, service).plan(**TRIP)

    outbound = sorted(
        q["outbound_date"]
        for q in service.queries
        if q.get("engine") == "google_flights"
    )
    assert outbound[0] == "2026-09-01"
    assert outbound[-1] <= "2026-09-19"


def test_a_stay_the_service_has_nowhere_for_drops_that_candidate() -> None:
    class Nowhere(Service):
        def get(self, url: str, *, params: dict[str, Any]) -> Answer:
            if params.get("engine") == "google_hotels":
                return Answer({"properties": []})
            return super().get(url, params=params)

    read = _planner(Cora(), Nowhere()).plan(**TRIP)

    assert "no prices" in read


def test_two_plans_in_one_conversation_keep_only_the_latest() -> None:
    cora = Cora()
    planner = _planner(cora, Service())

    planner.plan(**TRIP)
    planner.plan(**(TRIP | {"destination": "Porto"}))

    assert plan_from(json.loads(cora.kept[KEPT])).destination == "Porto"


def test_the_kept_plan_is_the_one_that_was_offered() -> None:
    cora = Cora()

    read = _planner(cora, Service()).plan(**TRIP)
    kept = plan_from(json.loads(cora.kept[KEPT]))

    assert f"total: EUR {kept.total:g}" in read


def test_a_departure_the_service_choked_on_does_not_lose_the_others() -> None:
    class Patchy(Service):
        def get(self, url: str, *, params: dict[str, Any]) -> Answer:
            if params.get("outbound_date") == "2026-09-01":
                raise __import__("httpx").ConnectError("down")
            return super().get(url, params=params)

    read = _planner(Cora(), Patchy()).plan(**TRIP)

    assert "total: EUR" in read


def test_the_shape_is_asked_for_with_what_the_traveller_wanted() -> None:
    cora = Cora()

    _planner(cora, Service()).plan(**(TRIP | {"wants": "no early flights"}))

    assert "no early flights" in cora.tasks[0]


def test_a_datetime_free_planner_needs_no_clock() -> None:
    """Every date in a plan comes from the window or the service, never from today."""
    cora = Cora()

    read = _planner(cora, Service()).plan(**TRIP)

    assert datetime.date.today().isoformat() not in read
