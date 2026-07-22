from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol


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


class ValidationRule(Protocol):
    def apply(self, user_input: str) -> None: ...


@dataclass(frozen=True)
class Plugin:
    system_prompt: str
    tools: tuple[Tool, ...]
    validation_rules: tuple[ValidationRule, ...]
    seed_docs: tuple[tuple[str, bytes], ...] = ()
