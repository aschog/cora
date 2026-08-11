import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol


class ToolRefusal(Exception):
    """Raised by a tool that will not run on the input it was given. The message
    is written for whoever reads it — the model, the log, the user's trace — and
    is the only exception text passed on: anything else that escapes a tool could
    be carrying whatever the tool was holding."""


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    parameter_schema: dict[str, Any]
    run: Callable[..., Any]


@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: dict[str, Any]
    call_id: str


@dataclass(frozen=True)
class ToolResult:
    call_id: str
    payload: Any = None
    error: str | None = None

    def __post_init__(self) -> None:
        if (self.payload is None) == (self.error is None):
            raise ValueError("a ToolResult carries exactly one of payload or error")

    def render(self) -> str:
        if self.error is not None:
            return self.error
        if isinstance(self.payload, str):
            return self.payload
        return json.dumps(self.payload, default=str)


class ValidationRule(Protocol):
    def apply(self, user_input: str) -> None: ...


@dataclass(frozen=True)
class Plugin:
    """`grounding` is the domain's answer to "may this be answered without the
    documents?". Empty means yes, and the model decides alone. Any other value is
    the reminder sent back to a model that answered without searching — worded by
    the plugin, because which questions belong to the documents is domain policy."""

    system_prompt: str
    tools: tuple[Tool, ...]
    validation_rules: tuple[ValidationRule, ...]
    seed_docs: tuple[tuple[str, bytes], ...] = ()
    grounding: str = ""
