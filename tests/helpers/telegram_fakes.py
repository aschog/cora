"""The Bot API as a list, for the suites that drive cora's Telegram frontend.

Beside `sse.py` for the same reason: what a frontend is reached through is the one
thing its tests may not use for real, and the fake is worth writing once.
"""

from collections.abc import Iterator
from typing import Any

from app_builder import assembled
from cora.app.assembly import App
from cora.frontends.telegram.bot import Message
from cora.ports.chat_model import ChatModel, ModelReply
from cora.ports.host import Extension
from fakes import ScriptedChatModel

ALLOWED = 11
STRANGER = 22


class FakeTelegram:
    """The two calls the bot is written against: the messages scripted in, and what it
    sent read back off the list it appended to."""

    def __init__(self, *incoming: Message) -> None:
        self._incoming = incoming
        self.sent: list[tuple[int, str]] = []

    def messages(self) -> Iterator[Message]:
        yield from self._incoming

    def send(self, chat: int, text: str) -> None:
        self.sent.append((chat, text))

    @property
    def texts(self) -> list[str]:
        return [text for _, text in self.sent]


def chatting(
    *,
    chat_model: ChatModel | None = None,
    plugin: Extension | None = None,
    answers: str = "ok",
    **overrides: Any,
) -> App:
    """An assembled app whose model answers in prose, for a test whose subject is the
    chat rather than the turn."""
    return assembled(
        chat_model=chat_model or ScriptedChatModel([ModelReply(text=answers)] * 8),
        plugin=plugin,
        **overrides,
    )
