"""What a planned trip is, and the shape it travels in.

Held rather than narrated: the planner checks and revises this, and the save writes it.
Dates are dates inside and text across the schema boundary, so what the model reads and
what a person fills into a card are the same ISO days the service was asked about.
"""

import datetime
from dataclasses import dataclass, replace
from typing import Any

CURRENCY = "EUR"


@dataclass(frozen=True)
class Day:
    """One day of the trip, and whether what is planned needs the weather to hold."""

    on: datetime.date
    doing: tuple[str, ...] = ()
    outdoor: bool = False


@dataclass(frozen=True)
class Priced:
    """One thing that was priced, over the dates it covers, and the line it reads as."""

    price: float
    currency: str
    start: datetime.date
    end: datetime.date
    line: str


@dataclass(frozen=True)
class Plan:
    """A whole trip: where, when, what to do, and what it costs.

    `destination` is the place in the traveller's own words and `arrival` is the airport
    the flights were priced to, because the two engines read where a trip goes
    differently and a revision has to price the flights again. Blank where no flight was
    searched.

    `fare` and `stay` are absent where nothing priced them, and a plan missing either is
    unpriced rather than free — a deployment with no search key plans the days and says
    the money is unknown.
    """

    origin: str
    destination: str
    depart: datetime.date
    back: datetime.date
    arrival: str = ""
    days: tuple[Day, ...] = ()
    fare: Priced | None = None
    stay: Priced | None = None
    currency: str = CURRENCY

    @property
    def nights(self) -> int:
        return (self.back - self.depart).days

    @property
    def total(self) -> float | None:
        if self.fare is None or self.stay is None:
            return None
        return self.fare.price + self.stay.price


def _day(on: datetime.date, doing: tuple[str, ...], outdoor: bool) -> dict[str, Any]:
    return {"on": on.isoformat(), "doing": list(doing), "outdoor": outdoor}


def _priced(priced: Priced | None) -> dict[str, Any] | None:
    if priced is None:
        return None
    return {
        "price": priced.price,
        "currency": priced.currency,
        "start": priced.start.isoformat(),
        "end": priced.end.isoformat(),
        "line": priced.line,
    }


def written(plan: Plan) -> dict[str, Any]:
    """The plan as the schema describes it, with its dates as ISO text."""
    return {
        "origin": plan.origin,
        "destination": plan.destination,
        "arrival": plan.arrival,
        "depart": plan.depart.isoformat(),
        "back": plan.back.isoformat(),
        "days": [_day(day.on, day.doing, day.outdoor) for day in plan.days],
        "fare": _priced(plan.fare),
        "stay": _priced(plan.stay),
        "currency": plan.currency,
    }


def _read_day(written_day: Any) -> Day:
    return Day(
        on=datetime.date.fromisoformat(str(written_day["on"])),
        doing=tuple(written_day.get("doing", ())),
        outdoor=bool(written_day.get("outdoor", False)),
    )


def _read_priced(written_priced: Any) -> Priced | None:
    if not written_priced:
        return None
    return Priced(
        price=float(written_priced["price"]),
        currency=str(written_priced["currency"]),
        start=datetime.date.fromisoformat(str(written_priced["start"])),
        end=datetime.date.fromisoformat(str(written_priced["end"])),
        line=str(written_priced["line"]),
    )


def plan_from(given: Any) -> Plan:
    """The plan a written one came from.

    Raises:
        KeyError: A part the schema requires is missing.
        ValueError: A date cannot be read.
    """
    return Plan(
        origin=str(given["origin"]),
        destination=str(given["destination"]),
        arrival=str(given.get("arrival", "")),
        depart=datetime.date.fromisoformat(str(given["depart"])),
        back=datetime.date.fromisoformat(str(given["back"])),
        days=tuple(_read_day(day) for day in given.get("days", ())),
        fare=_read_priced(given.get("fare")),
        stay=_read_priced(given.get("stay")),
        currency=str(given.get("currency", CURRENCY)),
    )


def priced_with(plan: Plan, fare: Priced, stay: Priced) -> Plan:
    """The same trip, with these two prices on it."""
    return replace(plan, fare=fare, stay=stay, depart=fare.start, back=fare.end)
