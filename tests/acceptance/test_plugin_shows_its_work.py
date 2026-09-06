"""A plugin's own work appears on the trace, under the call it happened in.

The plugin, its registration and the whole turn are the real ones; the model is
scripted, which is the boundary a stub is for.
"""

from app_builder import assembled
from cora.domain.chat_result import ChatResult
from cora.domain.trace import ToolUse, WorkShown
from cora.engine.plugin_registry import load_plugins
from cora.ports.chat_model import ModelReply
from cora.ports.plugin import ToolCall
from fakes import ScriptedChatModel
from fixture_plugins.shows_its_work import (
    AT_LOAD,
    COUNTED,
    DETAIL,
    LOST,
    SIGNED,
    TOOL,
)

SHOWING = "fixture_plugins.shows_its_work"
THREAD = "shown"
QUESTION = "How many wrens are in the garden?"
REPORT = "Three wrens, and the goldcrests would not hold still."
ANSWER = "Three wrens."


def _turn() -> ScriptedChatModel:
    return ScriptedChatModel(
        [
            ModelReply(tool_calls=(ToolCall(name=TOOL, arguments={}, call_id="c1"),)),
            ModelReply(text=REPORT),
            ModelReply(text=ANSWER),
        ]
    )


def _called(answered: ChatResult) -> ToolUse:
    [call] = [step for step in answered.trace if isinstance(step, ToolUse)]
    return call


def test_a_plugin_s_own_lines_stand_under_the_call_they_were_said_in() -> None:
    app = assembled(chat_model=_turn(), plugins=load_plugins([SHOWING]))

    answered = app.agent.answer(QUESTION, THREAD)

    shown = [step for step in _called(answered).steps if isinstance(step, WorkShown)]
    assert [step.did for step in shown] == [COUNTED, SIGNED, LOST]
    assert answered.answer == ANSWER


def test_a_plugin_s_lines_and_a_delegated_loop_s_rounds_stand_together() -> None:
    app = assembled(chat_model=_turn(), plugins=load_plugins([SHOWING]))

    answered = app.agent.answer(QUESTION, THREAD)

    kinds = [type(step).__name__ for step in _called(answered).steps]
    assert kinds == ["WorkShown", "WorkShown", "WorkShown", "ModelDecision"]


def test_a_line_is_signed_by_cora_whatever_the_plugin_wrote_in_it() -> None:
    app = assembled(chat_model=_turn(), plugins=load_plugins([SHOWING]))

    answered = app.agent.answer(QUESTION, THREAD)

    shown = [step for step in _called(answered).steps if isinstance(step, WorkShown)]
    assert {step.plugin for step in shown} == {SHOWING}


def test_a_line_a_plugin_marked_as_gone_wrong_reads_as_failed() -> None:
    app = assembled(chat_model=_turn(), plugins=load_plugins([SHOWING]))

    answered = app.agent.answer(QUESTION, THREAD)

    failed = [step for step in _called(answered).steps if step.failed]
    assert [step.summary for step in failed] == [f"{SHOWING} {LOST}"]
    assert answered.answer == ANSWER


def test_a_reader_opens_the_line_and_reads_what_the_plugin_put_behind_it() -> None:
    app = assembled(chat_model=_turn(), plugins=load_plugins([SHOWING]))

    answered = app.agent.answer(QUESTION, THREAD)

    [counted] = [
        step
        for step in _called(answered).steps
        if isinstance(step, WorkShown) and step.did == COUNTED
    ]
    assert counted.detail == DETAIL


def test_no_line_stands_beside_the_call_instead_of_under_it() -> None:
    app = assembled(chat_model=_turn(), plugins=load_plugins([SHOWING]))

    answered = app.agent.answer(QUESTION, THREAD)

    assert [step for step in answered.trace if isinstance(step, WorkShown)] == []


def test_a_line_shown_while_the_plugin_loaded_is_nowhere_in_the_turn() -> None:
    app = assembled(chat_model=_turn(), plugins=load_plugins([SHOWING]))

    answered = app.agent.answer(QUESTION, THREAD)

    shown = [
        step
        for step in list(answered.trace) + list(_called(answered).steps)
        if isinstance(step, WorkShown)
    ]
    assert AT_LOAD not in [step.did for step in shown]
