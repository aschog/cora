"""What a plugin is: it is handed cora, and it registers what it has."""

import pytest

from app_builder import assembled, indexed
from cora.domain.errors import InputRejectedError
from cora.engine.host import STOPPED_EARLY
from cora.engine.plugin_registry import load_plugins
from cora.engine.retrieval_tool import SEARCH_TOOL_NAME
from cora.ports.chat_model import ModelReply
from cora.ports.plugin import ToolCall
from fakes import ScriptedChatModel

REGISTERING = "fixture_plugins.registering"
INSTRUCTIONS = "You are the registering test plugin. Echo what the user asks you to."
REFUSAL = "The registering plugin will not answer shouting."
ANSWER = "You said hello."
THREAD = "t1"


def _calling_echo() -> ModelReply:
    return ModelReply(
        tool_calls=(ToolCall(name="echo", arguments={"word": "hello"}, call_id="c1"),)
    )


@pytest.mark.integration
def test_a_plugin_registers_a_tool_an_instruction_and_a_rule() -> None:
    """All three contributions of one plugin, in one turn: the tool the model called,
    the instructions it was briefed with, and the rule that refused what came next."""
    model = ScriptedChatModel([_calling_echo(), ModelReply(text=ANSWER)])
    app = assembled(chat_model=model, plugins=load_plugins([REGISTERING]))

    answered = app.agent.answer("Say hello.", THREAD)

    assert answered.answer == ANSWER
    assert 'echo(word="hello")' in " ".join(step.summary for step in answered.trace)
    briefed = model.last_messages
    assert briefed is not None
    assert INSTRUCTIONS in briefed[0].content, (
        "the plugin's instructions head the brief"
    )

    with pytest.raises(InputRejectedError) as shouted:
        app.agent.answer("SAY HELLO", THREAD)

    assert shouted.value.user_message == REFUSAL


SUB_AGENT = "fixture_plugins.sub_agent"
NOTES = ("notes.md", b"squats stall on sleep, not on volume")


def _calling_research(question: str) -> ModelReply:
    return ModelReply(
        tool_calls=(
            ToolCall(name="research", arguments={"question": question}, call_id="c1"),
        )
    )


def _searching(query: str) -> ModelReply:
    return ModelReply(
        tool_calls=(
            ToolCall(name=SEARCH_TOOL_NAME, arguments={"query": query}, call_id="s1"),
        )
    )


@pytest.mark.integration
def test_a_plugins_tool_runs_a_turn_of_its_own_under_the_call_that_ran_it() -> None:
    """A sub-agent, written as a plugin and allowed by nothing in cora: the tool the
    model called ran a loop with the model itself, and what that loop did hangs under
    the call rather than beside it."""
    model = ScriptedChatModel(
        [
            _calling_research("why do squats stall?"),
            _searching("squats"),
            ModelReply(text="Sleep, not volume."),
            ModelReply(text="Your notes say sleep, not volume."),
        ]
    )
    app = indexed(assembled(chat_model=model, plugins=load_plugins([SUB_AGENT])), NOTES)

    answered = app.agent.answer("Why do my squats stall?", THREAD)

    assert answered.answer == "Your notes say sleep, not volume."
    [call] = [step for step in answered.trace if step.summary.startswith("research(")]
    assert [step.summary for step in call.steps] == [
        f"Decided to call {SEARCH_TOOL_NAME}",
        f'{SEARCH_TOOL_NAME}(query="squats") → 1 passage from notes.md',
        "Decided no tool was needed",
    ], "the loop's steps are the call's children, in the order it took them"
    assert all(not step.steps for step in call.steps), "and one level is enough here"


@pytest.mark.integration
def test_a_delegated_loop_that_overspends_reports_what_it_found_to_the_turn() -> None:
    """The budget a plugin's loop spends is its own, and running out of it costs the
    turn nothing: the loop is asked to write up what it had, the report says it stopped
    early, and the turn answers around it. What the rounds bought is not thrown away
    with the rounds — but it does not arrive claiming to be a whole answer either."""
    model = ScriptedChatModel(
        [
            _calling_research("why do squats stall?"),
            _searching("squats"),
            _searching("squats again"),
            _searching("squats once more"),
            ModelReply(text="Sleep came up in the notes; I did not reach volume."),
            ModelReply(text="Sleep, most likely — though the digging was cut short."),
        ]
    )
    app = indexed(assembled(chat_model=model, plugins=load_plugins([SUB_AGENT])), NOTES)

    answered = app.agent.answer("Why do my squats stall?", THREAD)

    assert answered.answer == "Sleep, most likely — though the digging was cut short."
    [call] = [step for step in answered.trace if step.summary.startswith("research(")]
    assert not call.failed, "a loop that learnt something did not fail its call"
    assert STOPPED_EARLY in call.detail, (
        "and the turn is told it is not the whole story"
    )
    assert "Sleep came up in the notes" in call.detail


@pytest.mark.integration
def test_a_delegated_loop_cites_no_number_the_turn_did_not_hand_out() -> None:
    """The turn searched and was handed `[1]` for one document. A loop numbering its own
    passages would hand out a second `[1]`, and the page would draw the reader a button
    onto the document the turn cited rather than the one the loop read."""
    model = ScriptedChatModel(
        [
            _searching("diet"),
            _calling_research("why do squats stall?"),
            _searching("squats"),
            ModelReply(text="Sleep, not volume [1]."),
            ModelReply(text="Protein is 1.6 g per kg [1], and squats stall on sleep."),
        ]
    )
    app = indexed(
        assembled(chat_model=model, plugins=load_plugins([SUB_AGENT])),
        ("diet.md", b"aim for 1.6 g of protein per kg"),
        NOTES,
    )

    answered = app.agent.answer("Protein, and why do squats stall?", THREAD)

    assert [(c.number, c.document) for c in answered.citations] == [(1, "diet.md")]
    [call] = [step for step in answered.trace if step.summary.startswith("research(")]
    assert "[1]" not in call.detail, (
        "what the loop answered carries no number of its own"
    )


@pytest.mark.integration
def test_what_a_delegated_loop_answered_reaches_the_turn_labelled() -> None:
    """The hop the label has to survive. A sub-agent's answer is prose, not passages,
    but it was built out of the user's documents — so an instruction planted in one
    reaches the turn's own model as untrusted material rather than as a tool's word."""
    model = ScriptedChatModel(
        [
            _calling_research("why do squats stall?"),
            _searching("squats"),
            ModelReply(text="Sleep, not volume."),
            ModelReply(text="Your notes say sleep."),
        ]
    )
    app = indexed(assembled(chat_model=model, plugins=load_plugins([SUB_AGENT])), NOTES)

    app.agent.answer("Why do my squats stall?", THREAD)

    briefed = model.last_messages
    assert briefed is not None
    [told] = [message for message in briefed if message.role == "tool"]
    assert "untrusted" in told.content.lower()
    assert "instructions" in told.content.lower()
    assert told.content.endswith("Sleep, not volume.")
