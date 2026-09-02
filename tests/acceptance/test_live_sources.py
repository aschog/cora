"""Story 9: cora reaches outside itself.

The whole path through the plugin that really ships it — registered under its own
field, calling a service, and coming back as material cora did not write. The network
is the one thing stubbed, which is the boundary a stub is for.
"""

from typing import Any

import pytest

from app_builder import assembled
from cora.domain.trace import ToolUse
from cora.engine.plugin_registry import load_plugin
from cora.engine.rounds import UNTRUSTED_NOTICE
from cora.plugins.travel import SCOPE
from cora.plugins.travel.forecast import FORECAST_TOOL_NAME
from cora.ports.chat_model import ModelReply
from cora.ports.plugin import ToolCall
from fakes import ScriptedChatModel

QUESTION = "Will I need a coat in Lisbon this weekend?"
ANSWER = "Pack a light jacket — Saturday brings rain, and the rest is mild."
LISBON = {
    "results": [
        {"name": "Lisbon", "country": "Portugal", "latitude": 38.7, "longitude": -9.1}
    ]
}
WEEKEND = {
    "daily": {
        "time": ["2026-09-05", "2026-09-06"],
        "temperature_2m_max": [24.4, 25.1],
        "temperature_2m_min": [17.2, 18.0],
        "weather_code": [1, 61],
    }
}
FORECAST = (
    "Lisbon, Portugal — 2026-09-05: 24/17°C, mainly clear; "
    "2026-09-06: 25/18°C, light rain"
)


class Service:
    """The forecast service, written out. Two calls: the place, then its days."""

    def __init__(self) -> None:
        self._answers = [LISBON, WEEKEND]
        self.calls = 0

    def get(self, url: str, *, params: dict[str, Any]) -> "Service":
        self.calls += 1
        self._body = self._answers.pop(0)
        return self

    def raise_for_status(self) -> None:
        return None

    def json(self) -> Any:
        return self._body


@pytest.fixture
def service(monkeypatch: pytest.MonkeyPatch) -> Service:
    """Stubbed where the client is built, which is the one place the network is
    reached. The plugin, its registration and the whole turn are the real ones."""
    written = Service()
    monkeypatch.setattr(
        "cora.plugins.travel.forecast._client", lambda: written, raising=True
    )
    return written


def test_a_question_needing_the_outside_world_is_answered_from_it(
    service: Service,
) -> None:
    """The story, end to end: the model asks for the forecast, reads what the service
    said behind the untrusted label, and answers in cora's own prose. The trace is the
    record of where that came from — no citation is handed out for a fetch, because
    there is no passage of the user's own to open."""
    model = ScriptedChatModel(
        [
            ModelReply(
                tool_calls=(
                    ToolCall(
                        name=FORECAST_TOOL_NAME,
                        arguments={"place": "Lisbon"},
                        call_id="f1",
                    ),
                )
            ),
            ModelReply(text=ANSWER),
        ]
    )
    app = assembled(
        chat_model=model,
        plugins=(load_plugin("cora.plugins.travel"),),
        scopes=(SCOPE,),
    )

    answered = app.agent.answer(QUESTION, "t1")

    assert service.calls == 2, "the place was resolved, then its days fetched"
    assert answered.answer == ANSWER
    assert answered.citations == (), "a fetched forecast is nobody's passage to cite"

    told = [message for message in model.last_messages or () if message.role == "tool"]
    assert [FORECAST in message.content for message in told] == [True]
    assert all(UNTRUSTED_NOTICE in message.content for message in told), (
        "what a service said reaches the model behind the label a passage carries"
    )

    [used] = [step for step in answered.trace if isinstance(step, ToolUse)]
    assert used.name == FORECAST_TOOL_NAME
    assert used.arguments == {"place": "Lisbon"}
    assert FORECAST in used.detail, "the trace carries what the answer does not"
    assert not used.failed
