import logging
from dataclasses import dataclass

from cora.core.ports.chat_model import ChatModel, Message, ModelReply
from cora.core.ports.plugin import Tool

MAX_LOGGED_CHARS = 120

log = logging.getLogger(__name__)


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
        log.debug(
            "chat request: %d messages [%s], last: %s",
            len(messages),
            ", ".join(message.role for message in messages),
            truncate(messages[-1].content) if messages else "",
        )
        reply = self.inner.complete(messages, tools)
        log.debug(
            "chat reply: tool calls [%s], text: %s",
            ", ".join(call.name for call in reply.tool_calls),
            truncate(reply.text),
        )
        return reply
