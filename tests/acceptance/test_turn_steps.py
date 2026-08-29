"""Where a turn is while it runs: the steps it walks, named as it enters them."""

import pytest

from app_builder import assembled
from cora.domain.chat_result import ChatResult
from cora.domain.errors import InputRejectedError, LlmError
from cora.engine.steps import SCREEN, WORK
from cora.ports.chat_model import ModelReply
from cora.ports.plugin import ToolCall
from fakes import FailingChatModel, ScriptedChatModel, add_tool
from fixture_plugins import make_plugin

THREAD = "t1"


def _calling(call_id: str) -> ModelReply:
    return ModelReply(
        tool_calls=(
            ToolCall(name="add", arguments={"a": 20, "b": 22}, call_id=call_id),
        )
    )


def _walked(result: ChatResult) -> list[str]:
    """The steps the turn entered, in the order it entered them."""
    return [
        named for named in (getattr(step, "step", "") for step in result.trace) if named
    ]


@pytest.mark.integration
def test_a_turn_names_the_steps_it_walked() -> None:
    """A turn the user can be told the shape of: admitted, worked, then answered."""
    app = assembled(chat_model=ScriptedChatModel([ModelReply(text="ok")]))

    answered = app.agent.answer("What is cora?", THREAD)

    assert _walked(answered) == ["screen", "work", "answer"]


@pytest.mark.integration
def test_a_screened_out_question_never_reaches_the_model() -> None:
    """The refusal is the screening step's, and it costs the turn nothing further: the
    model is two steps away and is never asked."""
    model = ScriptedChatModel([ModelReply(text="never said")])
    app = assembled(chat_model=model)

    with pytest.raises(InputRejectedError) as refused:
        app.agent.answer("   ", THREAD)

    assert refused.value.step == SCREEN
    assert model.completions == 0


@pytest.mark.integration
def test_the_rounds_of_a_turn_are_spent_in_the_working_step() -> None:
    """Two tool calls and the answer after them: every round falls between the marker
    the working step wrote and the one the answering step writes."""
    app = assembled(
        chat_model=ScriptedChatModel(
            [_calling("c1"), _calling("c2"), ModelReply(text="42 twice over.")]
        ),
        plugin=make_plugin(tools=(add_tool(),)),
    )

    answered = app.agent.answer("What is 20 + 22, twice?", THREAD)

    said = [step.summary for step in answered.trace]
    assert said[:2] == ["Started to screen", "Started to work"]
    assert said[-1] == "Started to answer"
    assert said[2:-1] == [
        "Decided to call add",
        "add(a=20, b=22) → 42",
        "Decided to call add",
        "add(a=20, b=22) → 42",
        "Decided no tool was needed",
    ]


@pytest.mark.integration
def test_an_unreachable_model_is_reported_as_the_working_step_s_failure() -> None:
    """The step the failure came out of is on the error, the sentence the user reads is
    the one the error always carried, and the thread answers the next question."""
    unreachable = LlmError()
    app = assembled(chat_model=FailingChatModel(unreachable))

    with pytest.raises(LlmError) as failed:
        app.agent.answer("What is cora?", THREAD)

    assert failed.value.step == WORK
    assert failed.value.user_message == LlmError().user_message

    answered = assembled(
        chat_model=ScriptedChatModel([ModelReply(text="Back again.")])
    ).agent.answer("And now?", THREAD)
    assert answered.answer == "Back again."
