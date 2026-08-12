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


@dataclass(frozen=True, kw_only=True)
class Plugin:
    """Everything but `name` is optional: a plugin contributes whatever it has, and a
    bundle of rules alone is as legitimate as a bundle of tools. Keyword-only so that
    declaration order is not API — a fifth kind of contribution is then a field with a
    default, not a break.

    `name` heads the plugin's section of the brief. `instructions` is that section —
    cora writes the preamble around it, so a plugin states its own business and no
    two plugins argue about what cora is.

    `scope` is the domain's answer to "may this be answered without the documents?".
    Empty means yes, and the model decides alone. Any other value is a phrase naming
    what this plugin's documents cover — "training and nutrition" — which cora words
    into the reminder it sends back to a model that answered without searching. A
    phrase because phrases join: two paragraphs would contradict each other."""

    name: str
    instructions: str = ""
    tools: tuple[Tool, ...] = ()
    validation_rules: tuple[ValidationRule, ...] = ()
    scope: str = ""
