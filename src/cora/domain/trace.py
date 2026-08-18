import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from cora.domain.prose import listed


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


def step_kinds() -> tuple[type[TraceStep], ...]:
    """Every kind of step the engine can put in a trace, found rather than listed: a
    kind added next sprint travels through a checkpoint and into the conversation store
    without anyone having to remember either file."""
    found: list[type[TraceStep]] = []
    pending = [TraceStep]
    while pending:
        for kind in pending.pop().__subclasses__():
            if kind not in found:
                found.append(kind)
                pending.append(kind)
    return tuple(found)


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
class MemoryUnread(TraceStep):
    @property
    def summary(self) -> str:
        return "Could not read what I remember about you — answering without it"

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
