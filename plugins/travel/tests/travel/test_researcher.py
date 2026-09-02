import pytest

from cora.engine.retrieval_tool import SEARCH_TOOL_NAME
from cora.plugins.travel.forecast import FORECAST_TOOL_NAME
from cora.plugins.travel.researcher import DEFAULT_ROUNDS, researching, rounds_from
from cora.ports.chat_model import ModelReply
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

    reported = researching(host)("three days in Lisbon")

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


def test_a_rounds_setting_that_is_not_a_number_is_refused_at_load() -> None:
    """At load rather than at the first question: a typo that silently became three
    rounds would be found by nobody, and the composition root names the plugin that
    raised."""
    with pytest.raises(ValueError) as refused:
        rounds_from({"rounds": "lots"})

    assert "rounds" in str(refused.value)


def test_the_rounds_it_asks_for_are_the_rounds_the_loop_spends() -> None:
    """The setting reaches the loop rather than sitting in a variable: a loop given one
    round makes one call, then the write-up the host asks for when it runs out."""
    digging = ModelReply(
        tool_calls=(
            ToolCall(name=SEARCH_TOOL_NAME, arguments={"query": "x"}, call_id="s1"),
        )
    )
    model = ScriptedChatModel([digging, digging, ModelReply(text=FOUND)])
    host = host_for("cora.plugins.travel", model=model, settings={"rounds": "1"})

    researching(host)("three days in Lisbon")

    assert model.completions == 3, "one round it was given, then the write-up"
