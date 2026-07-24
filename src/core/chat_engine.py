from dataclasses import dataclass

from core.chat_model import ChatModel, Message
from core.plugin import ToolResult


@dataclass(frozen=True)
class ChatResult:
    answer: str
    tool_results: tuple[ToolResult, ...] = ()


@dataclass(frozen=True)
class ChatEngine:
    chat_model: ChatModel

    def answer(self, user_input: str) -> ChatResult:
        messages = (Message(role="user", content=user_input),)
        reply = self.chat_model.complete(messages, ())
        return ChatResult(answer=reply.text)
