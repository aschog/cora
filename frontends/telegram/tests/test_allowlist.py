import logging

import pytest

from cora.frontends.telegram.bot import Message, answering
from cora.ports.chat_model import ModelReply
from fakes import ScriptedChatModel
from telegram_fakes import ALLOWED, STRANGER, FakeTelegram, chatting


def test_a_chat_the_deployment_names_is_answered() -> None:
    telegram = FakeTelegram(Message(ALLOWED, "How much protein?"))

    answering(chatting(), telegram, allowed=(ALLOWED,))

    assert [chat for chat, _ in telegram.sent] == [ALLOWED]


def test_a_chat_nobody_named_is_answered_with_nothing() -> None:
    model = ScriptedChatModel([ModelReply(text="ok")])
    telegram = FakeTelegram(Message(STRANGER, "How much protein?"))

    answering(chatting(chat_model=model), telegram, allowed=(ALLOWED,))

    assert telegram.sent == []
    assert model.completions == 0


def test_a_chat_nobody_named_does_not_hold_up_the_one_behind_it() -> None:
    telegram = FakeTelegram(
        Message(STRANGER, "let me in"), Message(ALLOWED, "How much protein?")
    )

    answering(chatting(), telegram, allowed=(ALLOWED,))

    assert [chat for chat, _ in telegram.sent] == [ALLOWED]


def test_a_chat_nobody_named_is_named_in_the_log_and_nothing_it_said(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Where else an operator would find the number to allow: cora answers nobody until
    it is told a chat id, and the chat is the only thing that knows its own."""
    telegram = FakeTelegram(Message(STRANGER, "my secret question"))

    with caplog.at_level(logging.INFO, logger="cora.frontends.telegram.bot"):
        answering(chatting(), telegram, allowed=(ALLOWED,))

    assert str(STRANGER) in caplog.text
    assert "secret" not in caplog.text
