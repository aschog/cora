"""What a plan must satisfy before it is offered, one rule per function.

Arithmetic rather than opinion: whether a total exceeds a budget is not a thing to ask a
model, and a loop can only revise what it can reliably tell has failed. Every rule
answers with a sentence or with nothing, and nothing here raises — a failed rule is
something the planner reads and acts on, not an error.
"""

import datetime
from collections.abc import Callable, Mapping
from dataclasses import dataclass

from cora.plugins.travel.plan import Plan

WET = ("rain", "shower", "snow", "storm", "thunder")
"""What a forecast has to say for an outdoor day to be ruled out. Words rather than a
code, because the forecast arrives already read into prose a person would recognise."""


@dataclass(frozen=True)
class Asked:
    """What the traveller actually stated, and nothing cora inferred for them.

    Every field is absent by default: an absent budget is absent, never a budget of
    zero, so a rule the traveller did not give is a rule that cannot fail.
    """

    nights: int | None = None
    budget: int | None = None


def stay_covers_the_nights(plan: Plan, asked: Asked) -> str | None:
    """The stay has to cover every night between arriving and flying home."""
    if plan.stay is None:
        return None
    if plan.stay.start > plan.depart or plan.stay.end < plan.back:
        return (
            f"the stay runs {plan.stay.start} to {plan.stay.end}, which does not cover "
            f"every night between {plan.depart} and {plan.back}"
        )
    return None


def within_the_budget(plan: Plan, asked: Asked) -> str | None:
    """The fare and the stay together have to fit what the traveller said they had."""
    total = plan.total
    if asked.budget is None or total is None or total <= asked.budget:
        return None
    return (
        f"the trip comes to {total:g} {plan.currency}, which is "
        f"{total - asked.budget:g} over the {asked.budget} budget"
    )


def every_day_has_something(plan: Plan, asked: Asked) -> str | None:
    """Every date of the trip has to carry something to do."""
    doing = {day.on: day.doing for day in plan.days}
    empty = [day.isoformat() for day in _dates(plan) if not doing.get(day)]
    if not empty:
        return None
    return f"nothing is planned for {', '.join(empty)}"


def nights_match_what_was_asked(plan: Plan, asked: Asked) -> str | None:
    """A three-night trip is three nights, whatever the cheapest week happens to be."""
    if asked.nights is None or plan.nights == asked.nights:
        return None
    return f"the trip is {plan.nights} nights, and {asked.nights} were asked for"


def _dates(plan: Plan) -> list[datetime.date]:
    return [plan.depart + datetime.timedelta(days=step) for step in range(plan.nights)]


def outdoors_when_the_weather_holds(
    plan: Plan, forecast: Mapping[str, str]
) -> str | None:
    """A day planned outdoors cannot sit under a forecast that rules it out."""
    ruled_out = [
        day.on.isoformat()
        for day in plan.days
        if day.outdoor
        and any(wet in forecast.get(day.on.isoformat(), "").lower() for wet in WET)
    ]
    if not ruled_out:
        return None
    return f"the forecast rules out what is planned outdoors on {', '.join(ruled_out)}"


RULES: tuple[Callable[[Plan, Asked], str | None], ...] = (
    stay_covers_the_nights,
    within_the_budget,
    every_day_has_something,
    nights_match_what_was_asked,
)
"""Every rule that needs only the plan and what was asked for. A rule somebody wants
later is a function above and a line here, never a branch inside `check`."""


def check(
    plan: Plan, asked: Asked, forecast: Mapping[str, str] | None = None
) -> tuple[str, ...]:
    """Every rule this plan fails, as sentences, or nothing where it holds.

    All of them rather than the first: a near-miss offered to the traveller says
    everything that is wrong with it, not the earliest thing.

    Args:
        forecast: What the sky is doing, by ISO date. Absent where nothing was
            fetched, which makes the weather rule one that cannot fail.
    """
    failed = [rule(plan, asked) for rule in RULES]
    if forecast is not None:
        failed.append(outdoors_when_the_weather_holds(plan, forecast))
    return tuple(said for said in failed if said is not None)
