"""What a turn did, in the words the user reads it in."""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from cora.domain.prose import listed


class TraceStep(ABC):
    """One thing the turn did, worded for the user rather than for a log.

    A step fills `detail` and `failed` in as fields when it has them to give.
    """

    @property
    @abstractmethod
    def summary(self) -> str:
        """The one line the step is shown as."""
        ...

    @property
    def detail(self) -> str:
        """What is behind the line, for a reader who opens it — nothing, by default."""
        return ""

    @property
    def failed(self) -> bool:
        """Whether this step went wrong.

        A failed step is still shown: a turn that answered around a failure says so.
        """
        return False


def step_kinds() -> tuple[type[TraceStep], ...]:
    """Every kind of step the engine can put in a trace, found rather than listed.

    A kind added next sprint travels through a checkpoint and into the conversation
    store without anyone having to remember either file.
    """
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
    """A round of thinking: what the model decided to do next, and why it said it would.

    `detail` is the model's own prose from that round, which is thinking rather than
    answer — an empty `tools` is the round that ended the turn.
    """

    detail: str = ""
    tools: tuple[str, ...] = ()

    @property
    def summary(self) -> str:
        """What the model decided, named by the tools it asked for."""
        if not self.tools:
            return "Decided no tool was needed"
        return f"Decided to call {listed(self.tools)}"


@dataclass(frozen=True)
class MemoryUnread(TraceStep):
    """The turn could not read what cora remembers, and answered without it."""

    @property
    def summary(self) -> str:
        """That memory could not be read, and the turn went on without it."""
        return "Could not read what I remember about you — answering without it"

    @property
    def failed(self) -> bool:
        """Always true: this step exists only because something went wrong."""
        return True


@dataclass(frozen=True)
class ToolUse(TraceStep):
    """One tool call and what came back from it.

    `outcome` is the one line the user reads; `detail` is what the tool returned, and
    for a failed call it is the refusal rather than the payload.
    """

    name: str
    arguments: dict[str, Any] = field(default_factory=dict)
    outcome: str = ""
    detail: str = ""
    failed: bool = False

    @property
    def summary(self) -> str:
        """The call as it was made, with its outcome after an arrow."""
        return f"{self.name}({_arguments(self.arguments)}) → {self.outcome}"


def _arguments(arguments: dict[str, Any]) -> str:
    return ", ".join(
        f"{name}={json.dumps(value, default=str)}" for name, value in arguments.items()
    )
