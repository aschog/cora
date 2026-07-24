from dataclasses import dataclass
from typing import Literal

from core.plugin import ToolCall

Role = Literal["system", "user", "assistant", "tool"]


@dataclass(frozen=True)
class Message:
    role: Role
    content: str


@dataclass(frozen=True)
class ModelReply:
    text: str = ""
    tool_calls: tuple[ToolCall, ...] = ()

    @property
    def is_final(self) -> bool:
        return not self.tool_calls
