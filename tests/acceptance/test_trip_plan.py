"""One instruction plans a whole trip, and the plan is checked before it is offered.

The plugin, its planning loop and the whole turn are the real ones; the model and the
search service are stubbed, which is the boundary a stub is for.
"""

from typing import Any

import pytest

from app_builder import assembled
from cora.domain.trace import ToolUse
from cora.engine.host import ANSWER_TOOL_NAME
from cora.engine.plugin_registry import load_plugin
from cora.plugins.travel import SCOPE
from cora.plugins.travel.planner import PLAN_TOOL_NAME, REVISE_TOOL_NAME
from cora.ports.chat_model import ModelReply
from cora.ports.plugin import ToolCall
from fakes import ScriptedChatModel

KEY = "a-key"
THREAD = "the-trip-i-planned"
QUESTION = "Three days in Lisbon somewhere in September, under 800 all in."
ANSWER = "Two nights either side of the 8th, and it comes to 340 euros."
BUDGET = 800
CHEAPEST = "2026-09-08"
FARES = {"2026-09-01": 600.0, "2026-09-08": 100.0, "2026-09-15": 450.0}
STAY = 240.0
TRIP: dict[str, Any] = {
    "origin": "BER",
    "destination": "Lisbon",
    "arrival": "LIS",
    "window_start": "2026-09-01",
    "window_end": "2026-09-22",
    "nights": 3,
    "budget": BUDGET,
}
SHAPE: dict[str, Any] = {
    "days": [
        {"on": "2026-09-01", "doing": ["Alfama"], "outdoor": False},
        {"on": "2026-09-02", "doing": ["Belem"], "outdoor": False},
        {"on": "2026-09-03", "doing": ["Nishiki market"], "outdoor": False},
    ]
}
SHAPE_REPLY = ModelReply(
    tool_calls=(ToolCall(name=ANSWER_TOOL_NAME, arguments=SHAPE, call_id="d1"),)
)


class Answer:
    def __init__(self, body: dict[str, Any]) -> None:
        self._body = body

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return self._body


class Service:
    """The search service written out, pricing a fare by the week it departs so the
    window really has a cheapest one in it."""

    def __init__(self) -> None:
        self.queries: list[dict[str, Any]] = []

    def get(self, url: str, *, params: dict[str, Any]) -> Answer:
        self.queries.append(dict(params))
        if params.get("engine") == "google_hotels":
            return Answer(
                {
                    "properties": [
                        {
                            "name": "Hotel Baixa",
                            "hotel_class": "3-star hotel",
                            "total_rate": {"extracted_lowest": STAY},
                        }
                    ]
                }
            )
        return Answer(
            {
                "best_flights": [
                    {
                        "flights": [{"airline": "TAP Air Portugal"}],
                        "price": FARES.get(params["outbound_date"], 500.0),
                    }
                ]
            }
        )


@pytest.fixture
def service(monkeypatch: pytest.MonkeyPatch) -> Service:
    written = Service()
    monkeypatch.setattr(
        "cora.plugins.travel.trips._client", lambda: written, raising=True
    )
    return written


def _planning(**over: Any) -> ModelReply:
    return ModelReply(
        tool_calls=(ToolCall(name=PLAN_TOOL_NAME, arguments=TRIP | over, call_id="p1"),)
    )


def _app(model: ScriptedChatModel) -> Any:
    return assembled(
        chat_model=model,
        plugins=(load_plugin("cora.plugins.travel"),),
        scopes=(SCOPE,),
        plugin_settings={"cora.plugins.travel": {"serpapi_key": KEY}},
    )


def _planned(answered: Any) -> ToolUse:
    [call] = [
        step
        for step in answered.trace
        if isinstance(step, ToolUse) and step.name == PLAN_TOOL_NAME
    ]
    return call


def test_one_instruction_comes_back_with_a_dated_priced_plan_that_holds(
    service: Service,
) -> None:
    """The criterion: a place, a month and a budget in — and out comes a day-by-day
    plan on a week that was really priced, inside the budget, with nothing failing."""
    model = ScriptedChatModel([_planning(), SHAPE_REPLY, ModelReply(text=ANSWER)])

    answered = _app(model).agent.answer(QUESTION, THREAD)

    plan = _planned(answered).detail
    assert f"{CHEAPEST} to 2026-09-11" in plan
    assert "TAP Air Portugal" in plan
    assert "Hotel Baixa" in plan
    assert "total: EUR 340" in plan
    assert f"{CHEAPEST}: Alfama" in plan
    assert "the plan holds" in plan
    assert answered.answer == ANSWER
    assert not _planned(answered).failed


def test_a_later_turn_revises_the_plan_this_conversation_already_holds(
    service: Service,
) -> None:
    model = ScriptedChatModel(
        [
            _planning(),
            SHAPE_REPLY,
            ModelReply(text=ANSWER),
            ModelReply(
                tool_calls=(
                    ToolCall(
                        name=REVISE_TOOL_NAME,
                        arguments={"change": "cheaper", "budget": 400},
                        call_id="r1",
                    ),
                )
            ),
            SHAPE_REPLY,
            ModelReply(text="Still 340."),
        ]
    )
    app = _app(model)

    app.agent.answer(QUESTION, THREAD)
    answered = app.agent.answer("Make it cheaper.", THREAD)

    [revised] = [
        step
        for step in answered.trace
        if isinstance(step, ToolUse) and step.name == REVISE_TOOL_NAME
    ]
    assert "BER to Lisbon" in revised.detail
    assert "the plan holds" in revised.detail
