"""A plugin sees what cora is about to answer with, and may hand back another answer.

The plugins, their registration and the whole turn are the real ones; the model is
scripted, which is the boundary a stub is for.
"""

import pathlib
from typing import Any

import pytest

from app_builder import assembled, indexed
from cora.adapters.file_output import FileOutput
from cora.domain.card import Answer
from cora.domain.decision import TurnPaused
from cora.domain.trace import HandlerRan
from cora.plugins.travel import SCOPE
from cora.plugins.travel.itinerary import ITINERARY_TOOL_NAME
from cora.ports.chat_model import ModelReply
from cora.ports.host import ANSWERING, Extension, Host
from cora.ports.plugin import ToolCall
from fakes import FakeConversations, ScriptedChatModel

THREAD = "checked"
QUESTION = "How do I reach the desk?"
TITLE = "kyoto"
PLAN = "Day 1 - Fushimi Inari."
NUMBER = "555-0134"
SPOKEN = f"Call the desk on {NUMBER}."
MARKER = "[redacted]"
REDACTED = f"Call the desk on {MARKER}."
NOTICE = " Checked."
REDACTING = "fixture_plugins.redacting"
NOTICING = "fixture_plugins.noticing"
BREAKING = "fixture_plugins.breaking"
NUMBERING = "fixture_plugins.numbering"


def _redact(answer: str) -> str:
    return answer.replace(NUMBER, MARKER)


def _notice(answer: str) -> str:
    return answer + NOTICE


def _break(answer: str) -> str:
    raise RuntimeError("the checker broke")


def _number(answer: str) -> Any:
    return 7


def _checking(handle: Any) -> Any:
    def extend(cora: Host) -> None:
        cora.register_handler(event=ANSWERING, handle=handle)

    return extend


def _plugin(module: str, handle: Any) -> Extension:
    return Extension(module=module, extend=_checking(handle))


def _saving() -> ModelReply:
    return ModelReply(
        tool_calls=(
            ToolCall(
                name=ITINERARY_TOOL_NAME,
                arguments={"title": TITLE, "itinerary": PLAN},
                call_id="s1",
            ),
        )
    )


def _travel() -> Extension:
    from cora.plugins.travel import extend

    return Extension(module="cora.plugins.travel", extend=extend)


def _asked(*plugins: Extension, text: str = SPOKEN) -> Any:
    app = assembled(
        chat_model=ScriptedChatModel([ModelReply(text=text)]), plugins=plugins
    )
    return app.agent.answer(QUESTION, THREAD)


def test_an_answer_is_redacted_before_the_reader_is_given_it() -> None:
    answered = _asked(_plugin(REDACTING, _redact))

    assert answered.answer == REDACTED
    assert NUMBER not in answered.answer


def test_a_handler_that_changes_nothing_changes_nothing() -> None:
    answered = _asked(_plugin(REDACTING, lambda answer: None))

    assert answered.answer == SPOKEN


def test_two_plugins_each_change_the_answer_in_the_order_they_loaded() -> None:
    answered = _asked(_plugin(REDACTING, _redact), _plugin(NOTICING, _notice))

    assert answered.answer == REDACTED + NOTICE


def test_a_handler_that_raises_leaves_the_answer_and_the_turn_standing() -> None:
    answered = _asked(_plugin(BREAKING, _break))

    assert answered.answer == SPOKEN
    [ran] = [
        step
        for step in answered.trace
        if isinstance(step, HandlerRan) and step.plugin == BREAKING
    ]
    assert ran.failed


def test_a_handler_handing_back_something_that_is_not_text_is_dropped() -> None:
    answered = _asked(_plugin(NUMBERING, _number))

    assert answered.answer == SPOKEN


def test_the_trace_names_the_plugin_that_changed_the_answer() -> None:
    answered = _asked(_plugin(REDACTING, _redact))

    [ran] = [
        step
        for step in answered.trace
        if isinstance(step, HandlerRan) and step.plugin == REDACTING
    ]
    assert ran.event == ANSWERING
    assert not ran.failed


def test_a_redacted_sentence_takes_its_citation_with_it() -> None:
    """Citations are read off the answer the handlers returned, so a claim a plugin
    removed does not leave a source standing under the answer."""

    def drop_the_second(answer: str) -> str:
        return answer.split(" Also")[0]

    app = indexed(
        assembled(
            chat_model=ScriptedChatModel(
                [
                    ModelReply(
                        text="Tram 28 runs east [1]. Also the market shuts [2]."
                    ),
                ]
            ),
            plugins=(_plugin(REDACTING, drop_the_second),),
        ),
        ("tram.md", b"Tram 28 runs from Martim Moniz to the east of the city."),
        ("market.md", b"The market closes on Mondays and reopens on Tuesday."),
    )
    app.knowledge_base.search("tram", k=2)

    answered = app.agent.answer(QUESTION, THREAD)

    assert answered.answer == "Tram 28 runs east [1]."


def test_a_turn_that_stopped_and_was_picked_up_checks_its_answer_once(
    tmp_path: pathlib.Path,
) -> None:
    """The point is the answer's, not a run's: a turn that parked in the gate never
    reached it, so the answer the reader is given was checked exactly once."""
    seen: list[str] = []

    def counting(answer: str) -> None:
        seen.append(answer)
        return None

    app = assembled(
        chat_model=ScriptedChatModel([_saving(), ModelReply(text=SPOKEN)]),
        plugins=(_travel(), _plugin(REDACTING, counting)),
        scopes=(SCOPE,),
        output=FileOutput.at(str(tmp_path / "output")),
    )

    with pytest.raises(TurnPaused):
        app.agent.answer(QUESTION, THREAD)
    app.agent.resume(Answer(action="s1"), THREAD)

    assert seen == [SPOKEN]


def test_the_answer_that_is_recorded_is_the_one_the_handlers_left() -> None:
    kept = FakeConversations()
    app = assembled(
        chat_model=ScriptedChatModel([ModelReply(text=SPOKEN)]),
        plugins=(_plugin(REDACTING, _redact),),
        conversations=kept,
    )

    app.agent.answer(QUESTION, THREAD)

    [turn] = kept.turns(THREAD)
    assert turn.result.answer == REDACTED
