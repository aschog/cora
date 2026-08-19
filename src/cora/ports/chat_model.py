from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal, Protocol

from cora.ports.plugin import Tool, ToolCall

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


TextSink = Callable[[str], None]
"""Where a model writes its reply as it writes it. A reply is still returned whole —
this is the same text arriving earlier, so a reader is not left watching a still page
for as long as a model takes."""


def unheard(_: str) -> None:
    """The sink of a caller that is not reading along. Every slot that takes one
    defaults to this, so streaming costs a caller who wants none of it nothing."""


class ChatModel(Protocol):
    def complete(
        self,
        messages: tuple[Message, ...],
        tools: tuple[Tool, ...],
        on_text: TextSink = unheard,
    ) -> ModelReply: ...
