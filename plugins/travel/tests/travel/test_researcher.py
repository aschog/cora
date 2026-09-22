import pytest

from cora.engine.host import STOPPED_EARLY
from cora.engine.retrieval_tool import SEARCH_TOOL_NAME
from cora.plugins.travel.forecast import FORECAST_TOOL_NAME, forecast_tool
from cora.plugins.travel.researcher import (
    researching,
    rounds_from,
)
from cora.ports.chat_model import ModelReply
from cora.ports.plugin import ToolCall
from fakes import ScriptedChatModel, host_for

FOUND = "Tram 28 runs from Martim Moniz, and the week is dry."


def _answering() -> ScriptedChatModel:
    return ScriptedChatModel([ModelReply(text=FOUND)])


def test_the_researcher_offers_its_loop_the_forecast_beside_the_documents() -> None:
    model = _answering()
    host = host_for("cora.plugins.travel", model=model)

    reported = researching(host, forecast_tool())("three days in Lisbon")

    assert reported == FOUND
    offered = {tool.name for tool in model.last_tools or ()}
    assert FORECAST_TOOL_NAME in offered
    assert SEARCH_TOOL_NAME in offered


@pytest.mark.parametrize("named", ["lots", "", "2.5", "0", "-1"], ids=repr)
def test_a_rounds_setting_that_is_not_a_whole_number_above_zero_is_refused(
    named: str,
) -> None:
    with pytest.raises(ValueError) as refused:
        rounds_from({"rounds": named})

    assert "rounds" in str(refused.value)


def test_the_rounds_it_asks_for_are_the_rounds_the_loop_spends() -> None:
    digging = ModelReply(
        tool_calls=(
            ToolCall(name=SEARCH_TOOL_NAME, arguments={"query": "x"}, call_id="s1"),
        )
    )
    script = [digging, digging, ModelReply(text=FOUND)]

    stinted = ScriptedChatModel(list(script))
    reported = researching(
        host_for("cora.plugins.travel", model=stinted, settings={"rounds": "1"})
    )("three days in Lisbon")

    allowed = ScriptedChatModel(list(script))
    answered = researching(host_for("cora.plugins.travel", model=allowed, settings={}))(
        "three days in Lisbon"
    )

    assert STOPPED_EARLY in reported, "one round bought one lookup, then the write-up"
    assert STOPPED_EARLY not in answered, "the default had a round left to answer in"
    assert stinted.completions == allowed.completions, (
        "which is why the call count cannot be what this test reads"
    )
