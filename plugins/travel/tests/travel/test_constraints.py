import datetime
from typing import Any

from cora.plugins.travel.constraints import Asked, check
from cora.plugins.travel.plan import Day, Plan, Priced

OUT = datetime.date(2026, 9, 7)
BACK = datetime.date(2026, 9, 10)
DAYS = (
    Day(on=OUT, doing=("Alfama",)),
    Day(on=OUT + datetime.timedelta(days=1), doing=("Belem",), outdoor=True),
    Day(on=OUT + datetime.timedelta(days=2), doing=("Market",)),
)


def _priced(price: float, start: datetime.date, end: datetime.date) -> Priced:
    return Priced(price=price, currency="EUR", start=start, end=end, line="a line")


def _plan(**over: Any) -> Plan:
    fields: dict[str, Any] = {
        "origin": "BER",
        "destination": "LIS",
        "depart": OUT,
        "back": BACK,
        "days": DAYS,
        "fare": _priced(180.0, OUT, BACK),
        "stay": _priced(240.0, OUT, BACK),
    }
    return Plan(**(fields | over))


def _asked(**over: Any) -> Asked:
    return Asked(**({"nights": 3, "budget": 800} | over))


def test_a_plan_that_holds_fails_nothing() -> None:
    assert check(_plan(), _asked()) == ()


def test_a_stay_that_does_not_cover_every_night_fails() -> None:
    short = _plan(stay=_priced(240.0, OUT, BACK - datetime.timedelta(days=1)))

    [failed] = check(short, _asked())
    assert "night" in failed


def test_a_total_over_the_budget_fails_and_says_by_how_much() -> None:
    dear = _plan(stay=_priced(700.0, OUT, BACK))

    [failed] = check(dear, _asked())
    assert "80" in failed


def test_a_date_in_the_range_with_nothing_to_do_fails() -> None:
    empty = _plan(days=(DAYS[0], Day(on=DAYS[1].on, doing=()), DAYS[2]))

    [failed] = check(empty, _asked())
    assert "2026-09-08" in failed


def test_an_outdoor_day_the_forecast_rules_out_fails() -> None:
    [failed] = check(_plan(), _asked(), {"2026-09-08": "heavy rain"})

    assert "2026-09-08" in failed


def test_a_plan_failing_three_rules_comes_back_with_all_three() -> None:
    broken = _plan(
        stay=_priced(900.0, OUT, BACK - datetime.timedelta(days=1)),
        days=(DAYS[0], DAYS[2]),
    )

    assert len(check(broken, _asked())) == 3


def test_an_unpriced_plan_is_not_over_a_budget_it_was_never_priced_against() -> None:
    assert check(_plan(fare=None, stay=None), _asked()) == ()
