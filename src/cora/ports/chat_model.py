"""What cora says to a model, and what it reads back — in cora's own words.

A provider's request and response shapes stay behind the port: the engine builds a
transcript of `Message`s and reads a `ModelReply`, and an adapter is what turns either
into whatever the wire wants.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal, Protocol

from cora.ports.plugin import Tool, ToolCall

Role = Literal["system", "user", "assistant", "tool"]


@dataclass(frozen=True)
class Message:
    """One line of the transcript the model is handed.

    Two fields belong to one role each: `tool_calls` to an `assistant` line, and
    `tool_call_id` to a `tool` line, which answers exactly one call and needs the id to
    say which.
    """

    role: Role
    content: str
    tool_calls: tuple[ToolCall, ...] = ()
    tool_call_id: str | None = None


@dataclass(frozen=True)
class ModelReply:
    """What one round with the model produced: prose, tool calls, or both.

    Both at once is a model narrating its way to a call, and that prose is no part of
    the answer — `Aside` is how a reader watching along is told so.
    """

    text: str = ""
    tool_calls: tuple[ToolCall, ...] = ()

    @property
    def is_final(self) -> bool:
        """Whether this reply is the answer: a round that asked for no tool."""
        return not self.tool_calls


@dataclass(frozen=True)
class Piece:
    """Text the model wrote, handed on as it was written."""

    text: str


@dataclass(frozen=True)
class Aside:
    """The pieces of this round were thinking, not answer.

    The round they were written in ended in a tool call, so they were the model talking
    its way to a decision. A reader shown them is told once, here, rather than left to
    work it out from what arrives next.
    """


Written = Piece | Aside

TextSink = Callable[[Written], None]


def unheard(_: Written) -> None:
    """Read nothing as it is written.

    The sink of a caller that is not following along. Every slot that takes one defaults
    to this, so streaming costs a caller who wants none of it nothing.
    """


class ChatModel(Protocol):
    """The model, asked one round at a time."""

    def complete(
        self,
        messages: tuple[Message, ...],
        tools: tuple[Tool, ...],
        on_text: TextSink = unheard,
    ) -> ModelReply:
        """Continue the transcript by one round.

        Args:
            messages: The transcript so far, oldest first, opening with the brief.
            tools: What the model may call this round; empty offers it none.
            on_text: Reads the prose as it is written. The reply still comes back
                whole, so a caller that wants only the whole passes nothing here.

        Raises:
            LlmError: The provider failed, or answered with nothing usable — a final
                with no text, an answer cut off at the token limit, or a tool call
                whose arguments never parsed.
        """
        ...
