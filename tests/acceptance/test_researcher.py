from typing import Any

import pytest

from app_builder import assembled, indexed
from cora.domain.trace import ToolUse
from cora.engine.plugin_registry import load_plugin
from cora.engine.retrieval_tool import SEARCH_TOOL_NAME
from cora.plugins.travel import SCOPE
from cora.plugins.travel.forecast import FORECAST_TOOL_NAME
from cora.plugins.travel.researcher import RESEARCH_TOOL_NAME
from cora.ports.chat_model import ModelReply
from cora.ports.plugin import ToolCall
from fakes import ScriptedChatModel

QUESTION = "What should I do with three days in Lisbon?"
ANSWER = "Three days is plenty: the tram east, the market, and a day for the coast."
REPORT = (
    "Tram 28 runs from Martim Moniz. The market closes Mondays. Warm and dry all week."
)
NOTES = ("lisbon.md", b"Tram 28 runs from Martim Moniz. The market closes Mondays.")
LISBON = {
    "results": [
        {"name": "Lisbon", "country": "Portugal", "latitude": 38.7, "longitude": -9.1}
    ]
}
WEEK = {
    "daily": {
        "time": ["2026-09-05"],
        "temperature_2m_max": [25.1],
        "temperature_2m_min": [18.0],
        "weather_code": [1],
    }
}


class Service:
    def __init__(self) -> None:
        self._answers = [LISBON, WEEK]

    def get(self, url: str, *, params: dict[str, Any]) -> "Service":
        self._body = self._answers.pop(0)
        return self

    def raise_for_status(self) -> None:
        return None

    def json(self) -> Any:
        return self._body


@pytest.fixture
def service(monkeypatch: pytest.MonkeyPatch) -> Service:
    written = Service()
    monkeypatch.setattr(
        "cora.plugins.travel.forecast._client", lambda: written, raising=True
    )
    return written


def test_a_broad_question_is_researched_not_answered_in_one_pass(
    service: Service,
) -> None:
    model = ScriptedChatModel(
        [
            # The turn asks its researcher, and answers from the one report it gets.
            ModelReply(
                tool_calls=(
                    ToolCall(
                        name=RESEARCH_TOOL_NAME,
                        arguments={"question": "three days in Lisbon"},
                        call_id="r1",
                    ),
                )
            ),
            # Inside the call: two lookups, then the loop writes up what it found.
            ModelReply(
                tool_calls=(
                    ToolCall(
                        name=SEARCH_TOOL_NAME,
                        arguments={"query": "Lisbon tram market"},
                        call_id="s1",
                    ),
                )
            ),
            ModelReply(
                tool_calls=(
                    ToolCall(
                        name=FORECAST_TOOL_NAME,
                        arguments={"place": "Lisbon"},
                        call_id="f1",
                    ),
                )
            ),
            ModelReply(text=REPORT),
            ModelReply(text=ANSWER),
        ]
    )
    app = indexed(
        assembled(
            chat_model=model,
            plugins=(load_plugin("cora.plugins.travel"),),
            scopes=(SCOPE,),
        ),
        NOTES,
        scope=SCOPE,
    )

    answered = app.agent.answer(QUESTION, "t1")

    assert answered.answer == ANSWER

    told = [m for m in (model.last_messages or ()) if m.role == "tool"]
    assert len(told) == 1, "the conversation carries the report, not each lookup"
    assert REPORT in told[0].content
    assert "Martim Moniz" not in "".join(
        m.content for m in (model.last_messages or ()) if m.role != "tool"
    ), "no passage the loop read reached the turn on its own"

    [call] = [step for step in answered.trace if isinstance(step, ToolUse)]
    assert call.name == RESEARCH_TOOL_NAME
    inside = [step for step in call.steps if isinstance(step, ToolUse)]
    assert [step.name for step in inside] == [SEARCH_TOOL_NAME, FORECAST_TOOL_NAME], (
        "the researcher's lookups are nested under the call that started them"
    )
    assert not any(step.failed for step in inside), (
        "and both of them worked, so the stubbed service is load-bearing here"
    )
