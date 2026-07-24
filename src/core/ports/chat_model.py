from dataclasses import dataclass
from typing import Literal, Protocol

from core.ports.plugin import Tool, ToolCall

Role = Literal["system", "user", "assistant", "tool"]


@dataclass(frozen=True)
class Message:
    role: Role
    content: str
    tool_calls: tuple[ToolCall, ...] = ()
    tool_call_id: str | None = None


@dataclass(frozen=True)
class ModelReply:
    text: str = ""
    tool_calls: tuple[ToolCall, ...] = ()

    @property
    def is_final(self) -> bool:
        return not self.tool_calls


class ChatModel(Protocol):
    def complete(
        self, messages: tuple[Message, ...], tools: tuple[Tool, ...]
    ) -> ModelReply: ...
