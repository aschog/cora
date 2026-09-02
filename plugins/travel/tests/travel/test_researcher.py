import pytest

from cora.engine.host import STOPPED_EARLY
from cora.engine.retrieval_tool import SEARCH_TOOL_NAME
from cora.plugins.travel import extend
from cora.plugins.travel.forecast import FORECAST_TOOL_NAME, forecast_tool
from cora.plugins.travel.researcher import (
    DEFAULT_ROUNDS,
    RESEARCH_TOOL_NAME,
    researching,
    rounds_from,
)
from cora.ports.chat_model import ModelReply
from cora.ports.host import TOOL
from cora.ports.plugin import ToolCall
from fakes import ScriptedChatModel, host_for

FOUND = "Tram 28 runs from Martim Moniz, and the week is dry."


def _answering() -> ScriptedChatModel:
    return ScriptedChatModel([ModelReply(text=FOUND)])


def test_the_researcher_offers_its_loop_the_forecast_beside_the_documents() -> None:
    """A trip question turns on what is written down and on what the weather will do,
    so the loop is handed both. Without the forecast passed in it could only ever
    answer from documents, which is the thing one pass already does."""
    model = _answering()
    host = host_for("cora.plugins.travel", model=model)

    reported = researching(host, forecast_tool())("three days in Lisbon")

    assert reported == FOUND
    offered = {tool.name for tool in model.last_tools or ()}
    assert FORECAST_TOOL_NAME in offered
    assert SEARCH_TOOL_NAME in offered


@pytest.mark.parametrize(
    ("settings", "expected"),
    [({}, DEFAULT_ROUNDS), ({"rounds": "1"}, 1), ({"rounds": "4"}, 4)],
    ids=["unset", "one", "four"],
)
def test_how_many_rounds_it_may_spend_is_the_deployments_to_set(
    settings: dict[str, str], expected: int
) -> None:
    """Read from the plugin's own slice of the environment, so a deployment can make
    the digging shallower or deeper without touching cora or this plugin."""
    assert rounds_from(settings) == expected


@pytest.mark.parametrize("named", ["lots", "", "2.5", "0", "-1"], ids=repr)
def test_a_rounds_setting_that_is_not_a_whole_number_above_zero_is_refused(
    named: str,
) -> None:
    """A typo that silently became three rounds would be found by nobody. What the
    operator reads is the plugin's own test — this one is only the reading."""
    with pytest.raises(ValueError) as refused:
        rounds_from({"rounds": named})

    assert "rounds" in str(refused.value)


def test_the_rounds_it_asks_for_are_the_rounds_the_loop_spends() -> None:
    """The setting reaches the loop rather than sitting in a variable.

    Read off *how* the loop ended rather than how many calls it made: given the same
    script, a loop allowed one round runs out and is written up, while one allowed the
    default answers within its rounds and is not. The call count is identical either
    way, so counting alone would pass for a researcher that ignored the setting
    entirely.
    """
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


def test_the_forecast_the_researcher_hands_its_loop_is_built_once() -> None:
    """Every `Forecast` builds an HTTP client of its own, and building one per question
    parses the certificate bundle again and reuses no connection from the last. So the
    tool is built where the plugin registers — once — and handed to every loop after
    that, which is what the registered forecast beside it already does."""
    model = ScriptedChatModel([ModelReply(text=FOUND), ModelReply(text=FOUND)])
    host = host_for("cora.plugins.travel", model=model)
    extend(host)
    [research] = [
        entry.value.run
        for entry in host.registered
        if entry.kind == TOOL and entry.value.name == RESEARCH_TOOL_NAME
    ]

    research(question="first")
    first = _forecast_offered(model)
    research(question="second")
    second = _forecast_offered(model)

    assert first is second


def _forecast_offered(model: ScriptedChatModel) -> object:
    return next(
        tool for tool in model.last_tools or () if tool.name == FORECAST_TOOL_NAME
    )
