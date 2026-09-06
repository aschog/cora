import datetime
from typing import Any

from cora.plugins.travel.plan import (
    PLAN_SCHEMA,
    Day,
    Plan,
    Priced,
    plan_from,
    written,
)

OUT = datetime.date(2026, 9, 7)
BACK = datetime.date(2026, 9, 10)


def _day(on: datetime.date, *doing: str, outdoor: bool = False) -> Day:
    return Day(on=on, doing=tuple(doing), outdoor=outdoor)


def _fare(price: float = 180.0) -> Priced:
    return Priced(
        price=price, currency="EUR", start=OUT, end=BACK, line="TAP, non-stop"
    )


def _stay(price: float = 240.0) -> Priced:
    return Priced(price=price, currency="EUR", start=OUT, end=BACK, line="Hotel Baixa")


def _plan(**over: Any) -> Plan:
    fields: dict[str, Any] = {
        "origin": "BER",
        "destination": "LIS",
        "depart": OUT,
        "back": BACK,
        "days": (
            _day(OUT, "Alfama"),
            _day(OUT + datetime.timedelta(days=1), "Belem", outdoor=True),
            _day(OUT + datetime.timedelta(days=2), "Market"),
        ),
        "fare": _fare(),
        "stay": _stay(),
    }
    return Plan(**(fields | over))


def test_a_plan_carries_the_nights_between_its_two_dates() -> None:
    assert _plan().nights == 3


def test_a_priced_plan_totals_its_fare_and_its_stay() -> None:
    assert _plan().total == 420.0


def test_a_plan_with_no_fare_and_no_stay_is_unpriced() -> None:
    unpriced = _plan(fare=None, stay=None)

    assert unpriced.unpriced
    assert unpriced.total is None


def test_a_plan_priced_on_one_side_only_is_still_unpriced() -> None:
    assert _plan(stay=None).unpriced


def test_a_priced_plan_is_not_unpriced() -> None:
    assert not _plan().unpriced


def test_a_plan_round_trips_through_its_schema_unchanged() -> None:
    assert plan_from(written(_plan())) == _plan()


def test_an_unpriced_plan_round_trips_unchanged() -> None:
    unpriced = _plan(fare=None, stay=None)

    assert plan_from(written(unpriced)) == unpriced


def test_what_is_written_carries_its_dates_as_text() -> None:
    assert written(_plan())["depart"] == "2026-09-07"


def test_the_schema_requires_the_parts_a_plan_cannot_be_read_without() -> None:
    assert set(PLAN_SCHEMA["required"]) == {
        "origin",
        "destination",
        "depart",
        "back",
        "days",
    }
