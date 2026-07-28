from dataclasses import dataclass

from cora.core.ports.chat_model import ChatModel, Message, ModelReply
from cora.core.ports.plugin import Tool

MAX_LOGGED_CHARS = 120


def truncate(text: str) -> str:
    if len(text) <= MAX_LOGGED_CHARS:
        return text
    return text[: MAX_LOGGED_CHARS - 1] + "…"


@dataclass(frozen=True)
class LoggingChatModel:
    inner: ChatModel

    def complete(
        self, messages: tuple[Message, ...], tools: tuple[Tool, ...]
    ) -> ModelReply:
        return self.inner.complete(messages, tools)
