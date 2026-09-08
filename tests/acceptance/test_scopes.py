"""What a scope does to a turn: the pin that fixes a conversation to one field, and the
reading of the question that stands in for a pin when there is none."""

import pytest

from app_builder import assembled
from cora.app.assembly import App
from cora.domain.card import Answer
from cora.domain.chat_result import ChatResult
from cora.domain.decision import TurnPaused
from cora.domain.trace import ScopeSettled
from cora.engine.steps import (
    CHOSEN,
    PINNED,
    WHICH_FIELD,
)
from cora.ports.chat_model import ModelReply
from fakes import FakeConversations, ScriptedChatModel
from fixture_plugins import make_plugin, make_tool

THREAD = "t1"
FITNESS, TRAVEL = "fitness", "travel"
BOTH = (FITNESS, TRAVEL)
BMI, ROUTE_TO = "bmi", "route_to"
COACH_QUESTION = "How much protein should I eat?"


def _two_scopes(
    *replies: ModelReply, offered: tuple[str, ...] = BOTH
) -> tuple[App, ScriptedChatModel]:
    """Two fields, each with a persona and a tool of its own, and nothing system-wide.

    The model comes back beside the app: what a turn was told and what it was
    offered are what a scope decides, and the model is where both are visible.
    """
    model = ScriptedChatModel(list(replies))
    return assembled(
        chat_model=model,
        conversations=FakeConversations(),
        plugins=(
            make_plugin(
                name="coaching",
                instructions="You are a fitness coach.",
                tools=(make_tool(BMI),),
                scope=FITNESS,
            ),
            make_plugin(
                name="trips",
                instructions="You are a travel companion.",
                tools=(make_tool(ROUTE_TO),),
                scope=TRAVEL,
            ),
        ),
        scopes=offered,
    ), model


def _briefed(model: ScriptedChatModel) -> str:
    assert model.last_messages is not None
    return model.last_messages[0].content


def _offered(model: ScriptedChatModel) -> set[str]:
    assert model.last_tools is not None
    return {tool.name for tool in model.last_tools}


def _focus(result: ChatResult) -> ScopeSettled:
    """The one step that says which field the turn ran in, and how it got there."""
    [settled] = [step for step in result.trace if isinstance(step, ScopeSettled)]
    return settled


def _answer(text: str) -> ModelReply:
    return ModelReply(text=text)


@pytest.mark.integration
def test_a_pinned_conversation_stays_in_its_field_and_reaches_nothing_else() -> None:
    """The story's own scenario, end to end: a conversation that turned out to be about
    one field is pinned to it, and every turn after that is a coach's — the travel tool
    is not refused, it is never offered, and the question is never read for a field
    again."""
    app, model = _two_scopes(
        _answer("routing"), _answer("ok"), _answer("ok"), _answer("ok")
    )

    app.agent.answer("What are you for?", THREAD)
    before = model.completions

    first = app.agent.answer(COACH_QUESTION, THREAD, pin=FITNESS)
    second = app.agent.answer("And creatine?", THREAD, pin=FITNESS)

    assert app.agent.pinned(THREAD) == FITNESS
    for answered in (first, second):
        assert _focus(answered) == ScopeSettled(scope=FITNESS, how=PINNED)
    assert "fitness coach" in _briefed(model)
    assert "travel companion" not in _briefed(model)
    assert BMI in _offered(model) and ROUTE_TO not in _offered(model)
    assert model.completions == before + 2, "a pinned turn is not routed"


@pytest.mark.integration
def test_a_question_that_fits_two_fields_is_put_to_the_user() -> None:
    """Guessing between two fields answers half the readers wrongly, and the fork is one
    the reader settles in a sentence. The stop comes before the brief is written, so the
    turn resumes as a turn of the field they chose — and the question is read once,
    because the reading is a step behind the stop rather than in front of it."""
    app, model = _two_scopes(_answer("fitness, travel"), _answer("Walk it in a day."))

    with pytest.raises(TurnPaused) as stopped:
        app.agent.answer("What should I take on a walking holiday?", THREAD)

    card = stopped.value.pending.card
    assert card.prompt == WHICH_FIELD
    assert [action.label for action in card.actions[:2]] == [FITNESS, TRAVEL]
    assert card.actions[0].note == "You are a fitness coach."

    resumed = app.agent.resume(Answer(action=TRAVEL), THREAD)

    assert resumed.answer == "Walk it in a day."
    assert _focus(resumed) == ScopeSettled(scope=TRAVEL, how=CHOSEN)
    assert ROUTE_TO in _offered(model) and BMI not in _offered(model)
