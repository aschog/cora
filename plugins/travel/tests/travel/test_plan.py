import datetime
from typing import Any

from cora.plugins.travel.plan import (
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


def test_a_priced_plan_totals_its_fare_and_its_stay() -> None:
    assert _plan().total == 420.0


def test_a_plan_priced_on_one_side_only_has_no_total() -> None:
    assert _plan(stay=None).total is None


def test_a_plan_round_trips_through_its_schema_unchanged() -> None:
    assert plan_from(written(_plan())) == _plan()
