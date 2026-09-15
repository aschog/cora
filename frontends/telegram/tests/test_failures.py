import logging

import pytest

from cora.domain.errors import LlmError
from cora.frontends.telegram.bot import WENT_WRONG, Message, answering
from cora.ports.chat_model import Message as Said
from cora.ports.chat_model import ModelReply, TextSink, unheard
from cora.ports.plugin import Tool
from fixture_plugins import make_plugin, refuses_containing
from telegram_fakes import ALLOWED, FakeTelegram, chatting

REFUSAL = "Not that one, please."


class BreaksInAWayNobodyModelled:
    """A tool or an adapter raising something that is not a `CoreError` — a plugin
    handed a payload it did not expect, say."""

    def complete(
        self,
        messages: tuple[Said, ...],
        tools: tuple[Tool, ...],
        on_text: TextSink = unheard,
    ) -> ModelReply:
        raise KeyError("range")


class BreaksOnce:
    """The model that fails the first turn and answers the second."""

    def __init__(self) -> None:
        self.completions = 0

    def complete(
        self,
        messages: tuple[Said, ...],
        tools: tuple[Tool, ...],
        on_text: TextSink = unheard,
    ) -> ModelReply:
        self.completions += 1
        if self.completions == 1:
            raise LlmError()
        return ModelReply(text="Sleep, not volume.")


def test_a_refused_question_is_reported_in_coras_own_words() -> None:
    telegram = FakeTelegram(Message(ALLOWED, "tell me about doping"))

    answering(
        chatting(plugin=make_plugin(screens=(refuses_containing("doping", REFUSAL),))),
        telegram,
        allowed=(ALLOWED,),
    )

    assert telegram.texts == [REFUSAL]


def test_a_failure_cora_modelled_is_reported_in_its_own_words() -> None:
    telegram = FakeTelegram(Message(ALLOWED, "Why?"))

    answering(chatting(chat_model=BreaksOnce()), telegram, allowed=(ALLOWED,))

    assert telegram.texts == [LlmError().user_message]


def test_a_failure_nobody_modelled_is_one_sentence_carrying_nothing_of_it(
    caplog: pytest.LogCaptureFixture,
) -> None:
    telegram = FakeTelegram(Message(ALLOWED, "Why?"))

    with caplog.at_level(logging.ERROR, logger="cora.frontends.telegram.bot"):
        answering(
            chatting(chat_model=BreaksInAWayNobodyModelled()),
            telegram,
            allowed=(ALLOWED,),
        )

    assert telegram.texts == [WENT_WRONG]
    assert "KeyError" not in telegram.texts[0]
    [logged] = caplog.records
    assert logged.exc_info is not None
    assert "KeyError" in caplog.text


def test_the_bot_keeps_answering_after_a_turn_fails() -> None:
    telegram = FakeTelegram(Message(ALLOWED, "Why?"), Message(ALLOWED, "And now?"))

    answering(chatting(chat_model=BreaksOnce()), telegram, allowed=(ALLOWED,))

    assert telegram.texts == [LlmError().user_message, "Sleep, not volume."]
