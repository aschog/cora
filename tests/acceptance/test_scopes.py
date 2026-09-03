"""What a scope does to a turn: the pin that fixes a conversation to one field, and the
reading of the question that stands in for a pin when there is none."""

import pytest

from app_builder import assembled
from cora.app.assembly import App
from cora.domain.chat_result import ChatResult
from cora.domain.decision import TurnPaused
from cora.domain.errors import InputRejectedError, ScopePinnedError
from cora.domain.trace import ScopeSettled
from cora.engine.steps import (
    BELONGS_TO_NONE,
    CHOSEN,
    NOTHING_CHOSEN_FIELD,
    PINNED,
    ROUTED,
    WHICH_FIELD,
)
from cora.ports.chat_model import ModelReply
from cora.ports.host import DEFAULT_SCOPE
from fakes import FakeConversations, ScriptedChatModel
from fixture_plugins import make_plugin, make_tool

THREAD = "t1"
FITNESS, TRAVEL = "fitness", "travel"
BOTH = (FITNESS, TRAVEL)
BMI, ROUTE_TO = "bmi", "route_to"
COACH_QUESTION = "How much protein should I eat?"
TRIP_QUESTION = "How early should I book the sleeper?"


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
def test_a_conversation_pinned_to_one_field_refuses_a_second() -> None:
    """A pin is what lets a thread be trusted to keep its field, so it is set once. The
    same pin sent again is the caller holding one, not moving it."""
    app, _ = _two_scopes(_answer("ok"), _answer("ok"))

    app.agent.answer(COACH_QUESTION, THREAD, pin=FITNESS)

    with pytest.raises(ScopePinnedError) as refused:
        app.agent.answer(TRIP_QUESTION, THREAD, pin=TRAVEL)
    assert FITNESS in refused.value.user_message
    assert app.agent.answer("Again?", THREAD, pin=FITNESS).answer == "ok"


@pytest.mark.integration
def test_a_question_that_was_refused_pins_the_conversation_to_nothing() -> None:
    """The screen runs before anything, so a refused question costs the thread nothing —
    and a pin is the one cost it could not pay back, because a pin cannot be undone."""
    app, _ = _two_scopes(_answer("ok"))

    with pytest.raises(InputRejectedError):
        app.agent.answer("   ", THREAD, pin=FITNESS)

    assert app.agent.pinned(THREAD) is None
    assert app.agent.answer(TRIP_QUESTION, THREAD, pin=TRAVEL).answer == "ok"


@pytest.mark.integration
def test_a_pin_a_refused_turn_asked_for_does_not_wait_for_the_next_turn() -> None:
    """A pin is a request one turn made, so it lasts one turn. Left in the thread, it
    would be promoted by whatever question came next — which asked for no field, and
    would be answered in one, and pinned to it for good."""
    app, _ = _two_scopes(_answer(FITNESS), _answer("Protein, then."))

    with pytest.raises(InputRejectedError):
        app.agent.answer("   ", THREAD, pin=TRAVEL)
    answered = app.agent.answer(COACH_QUESTION, THREAD)

    assert app.agent.pinned(THREAD) is None
    assert _focus(answered) == ScopeSettled(scope=FITNESS, how=ROUTED)


@pytest.mark.integration
def test_the_pin_binds_what_comes_next_and_not_what_came_before() -> None:
    """A turn is a record of how it ran. Pinning later must not rewrite it, which is
    what reopening the thread has to show."""
    app, _ = _two_scopes(_answer(TRAVEL), _answer("unscoped"), _answer("coached"))

    app.agent.answer(TRIP_QUESTION, THREAD)
    app.agent.answer(COACH_QUESTION, THREAD, pin=FITNESS)

    assert app.conversations is not None
    [earlier, later] = app.conversations.turns(THREAD)
    assert earlier.question == TRIP_QUESTION
    assert _focus(earlier.result) == ScopeSettled(scope=TRAVEL, how=ROUTED)
    assert _focus(later.result) == ScopeSettled(scope=FITNESS, how=PINNED)


@pytest.mark.integration
def test_an_unpinned_thread_is_read_afresh_every_turn() -> None:
    """Routing is a reading of one question rather than a decision about the
    conversation, so one unpinned thread can answer a turn in each field — and only a
    pin says otherwise."""
    app, model = _two_scopes(
        _answer(FITNESS),
        _answer("protein"),
        _answer(TRAVEL),
        _answer("book early"),
    )

    coached = app.agent.answer(COACH_QUESTION, THREAD)
    assert _focus(coached) == ScopeSettled(scope=FITNESS, how=ROUTED)
    assert BMI in _offered(model) and ROUTE_TO not in _offered(model)

    tripped = app.agent.answer(TRIP_QUESTION, THREAD)

    assert _focus(tripped) == ScopeSettled(scope=TRAVEL, how=ROUTED)
    assert ROUTE_TO in _offered(model) and BMI not in _offered(model)
    assert "travel companion" in _briefed(model)


@pytest.mark.integration
def test_a_question_that_fits_two_fields_is_put_to_the_user() -> None:
    """Guessing between two fields answers half the readers wrongly, and the fork is one
    the reader settles in a sentence. The stop comes before the brief is written, so the
    turn resumes as a turn of the field they chose — and the question is read once,
    because the reading is a step behind the stop rather than in front of it."""
    app, model = _two_scopes(_answer("fitness, travel"), _answer("Walk it in a day."))

    with pytest.raises(TurnPaused) as stopped:
        app.agent.answer("What should I take on a walking holiday?", THREAD)

    asked = stopped.value.pending.decision
    assert asked is not None
    assert asked.question == WHICH_FIELD
    assert [option.label for option in asked.options] == [FITNESS, TRAVEL]
    assert asked.options[0].note == "You are a fitness coach."

    resumed = app.agent.resume(TRAVEL, THREAD)

    assert resumed.answer == "Walk it in a day."
    assert _focus(resumed) == ScopeSettled(scope=TRAVEL, how=CHOSEN)
    assert ROUTE_TO in _offered(model) and BMI not in _offered(model)


@pytest.mark.integration
def test_the_field_the_reader_chose_survives_the_step_being_replayed() -> None:
    """A resumed step runs again from its first line, so the question must not be read
    again on the way back: a second reading landing on one field would answer in it and
    throw the reader's choice away — and the trace would say the question was read."""
    app, model = _two_scopes(_answer("fitness, travel"), _answer("Book it early."))

    with pytest.raises(TurnPaused):
        app.agent.answer("What should I take on a walking holiday?", THREAD)
    resumed = app.agent.resume(TRAVEL, THREAD)

    assert resumed.answer == "Book it early."
    assert _focus(resumed) == ScopeSettled(scope=TRAVEL, how=CHOSEN)
    assert model.completions == 2, "the question is read once, not once per resume"


@pytest.mark.integration
def test_choosing_no_field_answers_the_question_plainly() -> None:
    app, model = _two_scopes(_answer("fitness, travel"), _answer("Plainly, then."))

    with pytest.raises(TurnPaused):
        app.agent.answer("What should I take on a walking holiday?", THREAD)
    resumed = app.agent.resume(None, THREAD)

    assert resumed.answer == "Plainly, then."
    assert _focus(resumed) == ScopeSettled(
        scope=DEFAULT_SCOPE, how=NOTHING_CHOSEN_FIELD
    )
    assert not {BMI, ROUTE_TO} & _offered(model)


@pytest.mark.integration
def test_a_question_belonging_to_no_field_is_answered_in_the_default_scope() -> None:
    """A bare cora is a scope like any other rather than an absence of one, so a turn
    can always say which field it ran in."""
    app, model = _two_scopes(_answer("none"), _answer("Cora is an agent."))

    answered = app.agent.answer("What are you?", THREAD)

    assert _focus(answered) == ScopeSettled(scope=DEFAULT_SCOPE, how=BELONGS_TO_NONE)
    assert not {BMI, ROUTE_TO} & _offered(model)
    assert "fitness coach" not in _briefed(model)
    assert "travel companion" not in _briefed(model)
