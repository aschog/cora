"""The loop that plans a whole trip, and the two tools that enter it.

A tool whose `run` is a control loop of the plugin's own: it asks the model for the one
thing that is judgement — what to do on a Tuesday — and does the searching, the scoring
and the checking itself. The loop stops when a plan passes its checks or when the passes
run out, never because the model said it was finished: a loop can only revise what it
can reliably tell has failed, and a model asked whether it succeeded says yes.
"""

import datetime
import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

from cora.ports.host import Host
from cora.ports.plugin import Tool, ToolRefusal

from .constraints import Asked, check
from .forecast import skies
from .plan import (
    Day,
    Plan,
    plan_from,
    priced_with,
    written,
)
from .trips import Offer, Search, _day, _whole

PLAN_TOOL_NAME = "plan_trip"
PLAN_TOOL_DESCRIPTION = (
    "Plan a whole trip: work out the days, price the flights and somewhere to stay, "
    "check the plan against what the traveller asked for, and revise it until it "
    "holds. Call this once for a trip rather than searching piece by piece — the "
    "planning happens out of the way and you are handed the finished plan."
)
REVISE_TOOL_NAME = "revise_plan"
REVISE_TOOL_DESCRIPTION = (
    "Change the trip already planned in this conversation — cheaper, a week later, a "
    "day more — and check it again. Call this rather than planning from the start: "
    "what is revised is the plan that passed its checks."
)

KEPT = "plan"
"""What the plan is kept under, for the length of the conversation."""
BUDGET_KEPT = "budget"
"""What the plan was checked against, kept beside it.

Beside rather than inside, because a budget is what the traveller *asked*, not part of
the trip that came back — and a revision that names no new ceiling is a revision under
the old one, never one under none.
"""
PASSES = 2
"""How many revisions the loop may make before it offers what it has.

Two because a plan that is still failing after two narrowings is failing on something a
third would not fix — and the trace is what makes a wrong guess here visible.
"""
CANDIDATES = 3
"""How many departures are paired with a stay. The window is priced across every
departure it allows, and only the cheapest few are worth a second call each."""

SHAPE_TASK = (
    "Plan what to do on each of {nights} days in {destination}, from {depart}.\n\n"
    "{asked}\n\n"
    "Answer with JSON and nothing else: a list of "
    '{{"on": "YYYY-MM-DD", "doing": ["...", "..."], "outdoor": true|false}}, one per '
    "day, in order. Mark a day outdoor when what you planned needs the weather to "
    "hold. Use the user's own documents where they say anything about the place."
)
NARROWER = (
    "\n\nThe plan you gave failed these checks, so give a narrower one that does not: "
    "{failed}"
)
UNPRICED = (
    "No search service is configured, so this plan has no prices: the days are planned "
    "and everything that does not need a price has been checked."
)
NOTHING_KEPT = (
    "No trip has been planned in this conversation yet, so there is nothing to revise. "
    "Plan one first."
)
NO_PLAN = (
    "I could not work out a shape for these days, so there is nothing to check or "
    "price."
)
HELD = "the plan holds"
FAILED_HEAD = "the plan could not be made to satisfy: "


@dataclass(frozen=True)
class Trip:
    """What the traveller asked for, as the planner was given it."""

    origin: str
    destination: str
    window_start: datetime.date
    window_end: datetime.date
    nights: int
    budget: int | None = None
    currency: str = "EUR"
    note: str = ""

    @property
    def asked(self) -> Asked:
        return Asked(nights=self.nights, budget=self.budget)


def _trip_from(given: dict[str, Any]) -> Trip:
    budget = given.get("budget")
    return Trip(
        origin=str(given["origin"]),
        destination=str(given["destination"]),
        window_start=_day(given["window_start"], "window_start"),
        window_end=_day(given["window_end"], "window_end"),
        nights=_whole(given["nights"], "nights"),
        budget=int(budget) if budget is not None else None,
        currency=str(given.get("currency", "EUR")),
        note=str(given.get("wants", "")),
    )


def _days_from(written_days: str) -> tuple[Day, ...]:
    opened = written_days.find("[")
    closed = written_days.rfind("]")
    if opened < 0 or closed < opened:
        return ()
    try:
        read = json.loads(written_days[opened : closed + 1])
    except json.JSONDecodeError:
        return ()
    if not isinstance(read, list):
        return ()
    days: list[Day] = []
    for entry in read:
        if not isinstance(entry, dict) or "on" not in entry:
            continue
        try:
            on = datetime.date.fromisoformat(str(entry["on"]))
        except ValueError:
            continue
        doing = entry.get("doing") or ()
        days.append(
            Day(
                on=on,
                doing=tuple(str(each) for each in doing),
                outdoor=bool(entry.get("outdoor", False)),
            )
        )
    return tuple(days)


def _read_out(plan: Plan, failed: Sequence[str]) -> str:
    lines = [
        f"{plan.origin} to {plan.destination}, {plan.depart} to {plan.back}, "
        f"{plan.nights} nights"
    ]
    if plan.fare is not None:
        lines.append(f"flight: {plan.fare.line}")
    if plan.stay is not None:
        lines.append(f"stay: {plan.stay.line}")
    if plan.total is not None:
        lines.append(f"total: {plan.currency} {plan.total:g}")
    else:
        lines.append(UNPRICED)
    for day in plan.days:
        lines.append(f"{day.on}: {', '.join(day.doing) or 'nothing planned'}")
    lines.append(HELD if not failed else FAILED_HEAD + "; ".join(failed))
    return "\n".join(lines)


@dataclass(frozen=True)
class Planner:
    """The loop, closed over the host and the search it prices with.

    Closed over rather than handed them per call, because by the time the model calls
    this there is no host in scope — the same reason cora's own tools are built at
    assembly.
    """

    cora: Host
    search: Search | None = None
    weather: Callable[..., str] | None = None

    def plan(self, **given: Any) -> str:
        """Plan a whole trip and answer with it, however it came out.

        Raises:
            ToolRefusal: The call cannot be read.
        """
        return self._planned(_trip_from(given))

    def revise(self, change: str, **given: Any) -> str:
        """Change the trip already planned here, and check it again.

        Raises:
            ToolRefusal: Nothing has been planned in this conversation.
        """
        kept = self.cora.state.read(KEPT)
        if kept is None:
            raise ToolRefusal(NOTHING_KEPT)
        held = plan_from(json.loads(kept))
        window_start = given.get("window_start") or held.depart.isoformat()
        window_end = given.get("window_end") or held.back.isoformat()
        nights = given.get("nights") or held.nights
        # A change that names no ceiling is a change under the one already stated:
        # letting it fall away would relax a constraint the traveller gave.
        asked_for = self.cora.state.read(BUDGET_KEPT)
        budget = given.get("budget")
        if budget is None and asked_for is not None:
            budget = int(asked_for)
        return self._planned(
            _trip_from(
                {
                    "origin": held.origin,
                    "destination": held.destination,
                    "window_start": window_start,
                    "window_end": window_end,
                    "nights": nights,
                    "budget": budget,
                    "currency": held.currency,
                    "wants": change,
                }
            )
        )

    def _planned(self, trip: Trip) -> str:
        forecast = self._forecast(trip)
        best: Plan | None = None
        failed: tuple[str, ...] = ()
        latest: tuple[str, ...] = ()
        for attempt in range(PASSES + 1):
            days = self._shape(trip, latest)
            closest: tuple[Plan, tuple[str, ...]] | None = None
            for plan in self._candidates(trip, days):
                against = check(plan, trip.asked, forecast)
                if not against:
                    self.cora.show(f"the plan holds after {attempt + 1} pass(es)")
                    return self._kept(plan, trip)
                if closest is None or len(against) < len(closest[1]):
                    closest = (plan, against)
            if closest is not None:
                # This pass's own failures: what the next shape is asked to fix, and
                # what the reader sees under this pass rather than under the first.
                latest = closest[1]
                if best is None or len(latest) < len(failed):
                    best, failed = closest
            self.cora.show(
                f"pass {attempt + 1} found no plan that holds",
                detail="; ".join(latest),
                failed=True,
            )
        # `_candidates` never comes back empty — it answers with the unpriced plan
        # where it could price nothing — so the second arm is the type's and not a
        # path a turn can take.
        return _read_out(best, failed) if best is not None else NO_PLAN

    def _kept(self, plan: Plan, trip: Trip) -> str:
        self.cora.state.keep(KEPT, json.dumps(written(plan)))
        self.cora.state.keep(
            BUDGET_KEPT, None if trip.budget is None else str(trip.budget)
        )
        return _read_out(plan, ())

    def _shape(self, trip: Trip, failed: Sequence[str]) -> tuple[Day, ...]:
        task = SHAPE_TASK.format(
            nights=trip.nights,
            destination=trip.destination,
            depart=trip.window_start.isoformat(),
            asked=trip.note or "No further preferences were given.",
        )
        if failed:
            task += NARROWER.format(failed="; ".join(failed))
        return _days_from(self.cora.delegate(task))

    def _forecast(self, trip: Trip) -> dict[str, str] | None:
        if self.weather is None:
            return None
        try:
            return skies(
                self.weather(
                    trip.destination,
                    trip.window_start.isoformat(),
                    trip.window_end.isoformat(),
                )
            )
        except ToolRefusal:
            return None

    def _candidates(self, trip: Trip, days: tuple[Day, ...]) -> list[Plan]:
        bare = Plan(
            origin=trip.origin,
            destination=trip.destination,
            depart=trip.window_start,
            back=trip.window_start + datetime.timedelta(days=trip.nights),
            days=days,
            currency=trip.currency,
        )
        if self.search is None:
            return [bare]
        try:
            fares = self.search.fares(
                origin=trip.origin,
                destination=trip.destination,
                window_start=trip.window_start.isoformat(),
                window_end=trip.window_end.isoformat(),
                nights=trip.nights,
                currency=trip.currency,
                **({"max_price": trip.budget} if trip.budget is not None else {}),
            )
        except ToolRefusal as unpriced:
            self.cora.show("could not price the flights", detail=str(unpriced))
            return [bare]
        self.cora.show(f"priced {len(fares)} fares across the window")
        priced = [
            plan
            for fare in sorted(fares, key=lambda offer: offer.price)[:CANDIDATES]
            if (plan := self._with_a_stay(trip, days, bare, fare)) is not None
        ]
        if not priced:
            return [bare]
        return sorted(priced, key=lambda plan: plan.total or 0.0)

    def _with_a_stay(
        self, trip: Trip, days: tuple[Day, ...], bare: Plan, fare: Offer
    ) -> Plan | None:
        if self.search is None:
            return None
        try:
            rooms = self.search.rooms(
                destination=trip.destination,
                check_in=fare.start.isoformat(),
                check_out=fare.end.isoformat(),
                currency=trip.currency,
                **(
                    {"max_price": max(0, trip.budget - int(fare.price))}
                    if trip.budget is not None
                    else {}
                ),
            )
        except ToolRefusal as nowhere:
            self.cora.show(f"nothing to stay in for {fare.start}", detail=str(nowhere))
            return None
        room = min(rooms, key=lambda offer: offer.price)
        shifted = tuple(
            Day(
                on=fare.start + datetime.timedelta(days=step),
                doing=day.doing,
                outdoor=day.outdoor,
            )
            for step, day in enumerate(days)
        )
        return priced_with(
            Plan(
                origin=bare.origin,
                destination=bare.destination,
                depart=fare.start,
                back=fare.end,
                days=shifted,
                currency=trip.currency,
            ),
            fare.priced(trip.currency),
            room.priced(trip.currency),
        )


PLAN_SCHEMA_FIELDS: dict[str, Any] = {
    "type": "object",
    "properties": {
        "origin": {
            "type": "string",
            "description": "Where the trip starts, as an airport or city code.",
        },
        "destination": {
            "type": "string",
            "description": "Where it goes, in the traveller's own words.",
        },
        "window_start": {
            "type": "string",
            "format": "date",
            "description": "Earliest day the trip could start.",
        },
        "window_end": {
            "type": "string",
            "format": "date",
            "description": "Latest day it could end.",
        },
        "nights": {"type": "integer", "description": "How many nights away."},
        "budget": {
            "type": "integer",
            "description": (
                "The most the whole trip may cost. Leave out where none was given."
            ),
        },
        "currency": {"type": "string", "description": "Three-letter currency."},
        "wants": {
            "type": "string",
            "description": "What the traveller said they want out of the trip.",
        },
    },
    "required": ["origin", "destination", "window_start", "window_end", "nights"],
    "additionalProperties": False,
}

REVISE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "change": {
            "type": "string",
            "description": "What to change about the trip, in the traveller's words.",
        },
        "budget": {
            "type": "integer",
            "description": "A new ceiling, where they gave one.",
        },
        "nights": {"type": "integer", "description": "A new number of nights."},
        "window_start": {"type": "string", "format": "date"},
        "window_end": {"type": "string", "format": "date"},
    },
    "required": ["change"],
    "additionalProperties": False,
}


def planning_tools(
    cora: Host,
    search: Search | None = None,
    weather: Callable[..., str] | None = None,
) -> tuple[Tool, ...]:
    """The two tools that enter the loop, over one client where there is one."""
    planner = Planner(cora=cora, search=search, weather=weather)
    return (
        Tool(
            name=PLAN_TOOL_NAME,
            description=PLAN_TOOL_DESCRIPTION,
            parameter_schema=PLAN_SCHEMA_FIELDS,
            run=planner.plan,
            untrusted=True,
        ),
        Tool(
            name=REVISE_TOOL_NAME,
            description=REVISE_TOOL_DESCRIPTION,
            parameter_schema=REVISE_SCHEMA,
            run=planner.revise,
            untrusted=True,
        ),
    )
