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


@dataclass(frozen=True)
class Piece:
    """Text the model wrote, handed on as it was written."""

    text: str


@dataclass(frozen=True)
class Aside:
    """The round those pieces were written in ended in a tool call, so they were the
    model talking its way to a decision and are no part of the answer. A reader shown
    them is told once, here, rather than left to work it out from what arrives next."""


Written = Piece | Aside

TextSink = Callable[[Written], None]
"""Where a model writes its reply as it writes it. A reply is still returned whole —
the pieces are the same text arriving earlier, so a reader is not left watching a still
page for as long as a model takes. A turn may take several rounds, and only the last of
them is the answer: `Aside` is how a sink learns that the round it just read was one of
the others."""


def unheard(_: Written) -> None:
    """The sink of a caller that is not reading along. Every slot that takes one
    defaults to this, so streaming costs a caller who wants none of it nothing."""


class ChatModel(Protocol):
    def complete(
        self,
        messages: tuple[Message, ...],
        tools: tuple[Tool, ...],
        on_text: TextSink = unheard,
    ) -> ModelReply: ...
