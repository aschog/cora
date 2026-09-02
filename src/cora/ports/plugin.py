"""What a tool is, and the shape of a tool call from end to end."""

import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


class ToolRefusal(Exception):
    """Raised by a tool that will not run on the input it was given.

    The message is written for whoever reads it — the model, the log, the user's
    trace — and is the only exception text passed on: anything else that escapes a tool
    could be carrying whatever the tool was holding.
    """


@dataclass(frozen=True)
class Tool:
    """One thing the model can do, as the model is told about it.

    `name` is what the model calls and what the trace shows, so it is unique across
    every plugin loaded. `parameter_schema` is JSON Schema, validated against a call's
    arguments before `run` sees them; `run` is called with those arguments as keywords,
    and whatever it returns is rendered for the model — returning nothing is an error,
    because a tool that ran and said nothing is indistinguishable from one that failed.

    `untrusted` says that what this tool returns is material cora did not write — a
    service it called, a page it read. Declared here rather than read off the payload,
    because a fetched string and a calculated one are the same shape, and only the tool
    knows which it is. What a declaring tool returns reaches the model behind the same
    label a passage of the user's own documents does.
    """

    name: str
    description: str
    parameter_schema: dict[str, Any]
    run: Callable[..., Any]
    untrusted: bool = False


@dataclass(frozen=True)
class ToolCall:
    """One call the model asked for, with the arguments it wrote.

    `call_id` is the provider's, and it is what the answering `ToolResult` and the
    `tool` message carry back: a round may ask for the same tool twice.
    """

    name: str
    arguments: dict[str, Any]
    call_id: str


@dataclass(frozen=True)
class ToolResult:
    """What one call produced: a payload or a refusal, never both and never neither."""

    call_id: str
    payload: Any = None
    error: str | None = None

    def __post_init__(self) -> None:
        """Refuse a result that says nothing, or says two things.

        Raises:
            ValueError: Both a payload and an error were given, or neither was.
        """
        if (self.payload is None) == (self.error is None):
            raise ValueError("a ToolResult carries exactly one of payload or error")

    def render(self) -> str:
        """The result as the model reads it — the error, the text, or JSON."""
        if self.error is not None:
            return self.error
        if isinstance(self.payload, str):
            return self.payload
        return json.dumps(self.payload, default=str)
