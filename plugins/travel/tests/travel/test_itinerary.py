import datetime
import json
from typing import Any

import pytest

from cora.plugins.travel.itinerary import (
    ITINERARY_TOOL_NAME,
    NOT_THE_PLAN,
    NOTHING_PLANNED,
    flat,
    itinerary_tool,
)
from cora.plugins.travel.plan import Day, Plan, Priced, written
from cora.plugins.travel.planner import KEPT
from cora.ports.plugin import ToolRefusal
from fakes import FakeOutput

TITLE = "Kyoto, three days"
OUT = datetime.date(2026, 9, 7)
BACK = datetime.date(2026, 9, 10)


def _priced(price: float, line: str) -> Priced:
    return Priced(price=price, currency="EUR", start=OUT, end=BACK, line=line)


def _plan(**over: Any) -> Plan:
    fields: dict[str, Any] = {
        "origin": "BER",
        "destination": "Kyoto",
        "depart": OUT,
        "back": BACK,
        "days": (
            Day(on=OUT, doing=("Fushimi Inari at dawn",)),
            Day(on=OUT + datetime.timedelta(days=1), doing=("Arashiyama",)),
            Day(on=OUT + datetime.timedelta(days=2), doing=("Nishiki",)),
        ),
        "fare": _priced(180.0, "ANA, non-stop"),
        "stay": _priced(240.0, "Ryokan Ito"),
    }
    return Plan(**(fields | over))


class Cora:
    """The host the tool reads the verified plan from."""

    def __init__(self, plan: Plan | None = None) -> None:
        self.kept = {} if plan is None else {KEPT: json.dumps(written(plan))}

    @property
    def state(self) -> "Cora":
        return self

    def read(self, name: str) -> str | None:
        return self.kept.get(name)

    def keep(self, name: str, value: str | None) -> None:
        self.kept[name] = value or ""


def _tool(output: FakeOutput, plan: Plan | None = None) -> Any:
    return itinerary_tool(output, Cora(plan))  # ty: ignore[invalid-argument-type]


def test_the_tool_writes_the_verified_plan_and_says_where_it_went() -> None:
    """What the user keeps is a file they can open, and the turn has to be able to say
    where it went — an effect nobody can find is an effect that may as well not have
    happened."""
    output = FakeOutput()
    plan = _plan()

    said = _tool(output, plan).run(title=TITLE, **flat(plan))

    [(name, kept)] = output.written.items()
    assert "ANA, non-stop" in kept
    assert "2026-09-07: Fushimi Inari at dawn" in kept
    assert name.startswith("kyoto-three-days-") and name.endswith(".md")
    assert f"/kept/{name}" in said


def test_a_plan_that_is_not_the_one_checked_is_refused_and_nothing_is_written() -> None:
    """The model writes these arguments, so they are compared rather than trusted: the
    traveller approved the plan cora checked, not whatever arrived."""
    output = FakeOutput()
    arrived = flat(_plan()) | {"total": "EUR 100"}

    with pytest.raises(ToolRefusal, match=NOT_THE_PLAN):
        _tool(output, _plan()).run(title=TITLE, **arrived)

    assert output.written == {}


def test_a_save_with_no_plan_kept_refuses_rather_than_writing_an_empty_file() -> None:
    output = FakeOutput()

    with pytest.raises(ToolRefusal, match=NOTHING_PLANNED):
        _tool(output).run(title=TITLE, **flat(_plan()))

    assert output.written == {}


def test_the_tool_declares_that_it_changes_something_outside_cora() -> None:
    """The declaration is the whole reason the gate stops for it, and it is the tool's
    own to make: only the tool knows a call of it writes."""
    tool = _tool(FakeOutput())

    assert tool.name == ITINERARY_TOOL_NAME
    assert tool.effect
    assert not tool.untrusted, "what it answers is cora's own words, not a service's"


def test_a_title_that_leaves_no_filename_is_refused_not_renamed() -> None:
    """The title is the model's prose, so turning it into a name is the plugin's job.
    Nothing left of it is a refusal rather than an invented name."""
    output = FakeOutput()
    plan = _plan()

    with pytest.raises(ToolRefusal):
        _tool(output, plan).run(title="...", **flat(plan))

    assert output.written == {}


def test_two_plans_under_one_title_are_two_files() -> None:
    """A revised plan saved under the same title must not take the earlier one with it:
    this is a file the user approved and keeps."""
    output = FakeOutput()
    first, second = _plan(), _plan(back=BACK + datetime.timedelta(days=1))

    _tool(output, first).run(title=TITLE, **flat(first))
    _tool(output, second).run(title=TITLE, **flat(second))

    assert len(output.written) == 2
    assert all(name.startswith("kyoto-three-days-") for name in output.written)


def test_the_same_plan_saved_twice_is_one_file() -> None:
    """The name is made out of what was saved, so saving the identical plan again is the
    same file rather than a second copy of it."""
    output = FakeOutput()
    plan = _plan()

    _tool(output, plan).run(title=TITLE, **flat(plan))
    _tool(output, plan).run(title=TITLE, **flat(plan))

    assert len(output.written) == 1


def test_the_arguments_the_card_shows_are_the_plan_the_traveller_reads() -> None:
    """Flat and one field per part, because the gate lays out one read-only field per
    top-level argument: a plan inside one field is a plan nobody read."""
    shown = flat(_plan())

    assert shown["depart"] == "2026-09-07"
    assert shown["total"] == "EUR 420"
    assert shown["days"][0] == "2026-09-07: Fushimi Inari at dawn"


def test_an_unpriced_plan_says_so_rather_than_showing_a_price_of_nothing() -> None:
    shown = flat(_plan(fare=None, stay=None))

    assert shown["total"] == "unpriced"
    assert shown["flight"] == "unpriced"
