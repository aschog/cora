import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from cora.core.prose import listed


class TraceStep(ABC):
    """A step fills `detail` and `failed` in as fields when it has them to give."""

    @property
    @abstractmethod
    def summary(self) -> str: ...

    @property
    def detail(self) -> str:
        return ""

    @property
    def failed(self) -> bool:
        return False


@dataclass(frozen=True)
class ModelDecision(TraceStep):
    detail: str = ""
    tools: tuple[str, ...] = ()

    @property
    def summary(self) -> str:
        if not self.tools:
            return "Decided no tool was needed"
        return f"Decided to call {listed(self.tools)}"


@dataclass(frozen=True)
class Reconsidered(TraceStep):
    outcome: str = ""
    detail: str = ""
    failed: bool = False

    @property
    def summary(self) -> str:
        return f"Checked the documents and asked again → {self.outcome}"


@dataclass(frozen=True)
class SecondLookLost(TraceStep):
    @property
    def summary(self) -> str:
        return "The second look never came back — keeping the first answer"

    @property
    def failed(self) -> bool:
        return True


@dataclass(frozen=True)
class ToolUse(TraceStep):
    name: str
    arguments: dict[str, Any] = field(default_factory=dict)
    outcome: str = ""
    detail: str = ""
    failed: bool = False

    @property
    def summary(self) -> str:
        return f"{self.name}({_arguments(self.arguments)}) → {self.outcome}"


def _arguments(arguments: dict[str, Any]) -> str:
    return ", ".join(
        f"{name}={json.dumps(value, default=str)}" for name, value in arguments.items()
    )
