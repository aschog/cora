"""What a turn did, in the words the user reads it in."""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from functools import cache
from typing import Any, get_origin, get_type_hints

from cora.domain.prose import listed


class TraceStep(ABC):
    """One thing the turn did, worded for the user rather than for a log.

    A step fills `detail`, `failed` and `steps` in as fields when it has them to give.
    `steps` is what happened *inside* this one, which only a step that ran something
    else has: a trace is a tree, and most of it is one level deep.

    A kind that needs a `__post_init__` of its own calls `super().__post_init__()`, or
    it stops holding the tuples it declares once a turn has been through a checkpoint.
    """

    steps: tuple["TraceStep", ...] = ()

    def __post_init__(self) -> None:
        """Hold the tuples this kind declares, whatever it was handed.

        A step travels through a checkpoint and through the conversation store as data,
        and comes back as keyword arguments. JSON has one sequence, so a field declared
        a tuple returns a list, and a step would quietly stop being equal to the step
        that was recorded. Read off the kind's own declaration here, once, rather than
        at each door — both doors are reading the same declaration anyway.
        """
        for name in _tuple_fields(type(self)):
            held = getattr(self, name)
            if isinstance(held, list):
                object.__setattr__(self, name, tuple(held))

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


@cache
def _tuple_fields(kind: type["TraceStep"]) -> tuple[str, ...]:
    """Which of a kind's fields are declared tuples, worked out once per kind.

    Keyed by the class, which the cache then holds: the kinds are a fixed set declared
    in this module, so nothing accumulates. A kind declared inside a test would be held
    for the process and go on being found by `step_kinds`, which is a reason to declare
    them here rather than a reason not to cache.
    """
    return tuple(
        name
        for name, declared in get_type_hints(kind).items()
        if get_origin(declared) is tuple
    )


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
class StepEntered(TraceStep):
    """The turn entered a step, and is now in it.

    Where a turn is rather than what it did: the marker a step contributes before
    anything it goes on to do, so the steps that follow read as that step's.
    """

    step: str

    @property
    def summary(self) -> str:
        """The step by name, which every step of a turn is a verb for."""
        return f"Started to {self.step}"


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
class HandlerRan(TraceStep):
    """One plugin's handler took part in the turn, and this is what came of it.

    `plugin` is the module the deployment named, because that is who a reader holds
    responsible for an amendment they did not expect. `outcome` is the one line they
    read, worded for the event it happened at; `detail` carries the refusal, or the kind
    of exception a handler that broke was raising.
    """

    plugin: str = ""
    event: str = ""
    outcome: str = ""
    detail: str = ""
    failed: bool = False

    @property
    def summary(self) -> str:
        """The plugin, and what it did — the plugin first, because that is the news."""
        return f"{self.plugin} {self.outcome}"


@dataclass(frozen=True)
class ToolUse(TraceStep):
    """One tool call and what came back from it.

    `outcome` is the one line the user reads, and `detail` is what the tool returned —
    for a failed call the refusal rather than the payload. `steps` is what the tool did
    inside the call, which is empty unless the tool ran a loop of its own.
    """

    name: str
    arguments: dict[str, Any] = field(default_factory=dict)
    outcome: str = ""
    detail: str = ""
    failed: bool = False
    steps: tuple[TraceStep, ...] = ()

    @property
    def summary(self) -> str:
        """The call as it was made, with its outcome after an arrow."""
        return f"{self.name}({_arguments(self.arguments)}) → {self.outcome}"


def _arguments(arguments: dict[str, Any]) -> str:
    return ", ".join(
        f"{name}={json.dumps(value, default=str)}" for name, value in arguments.items()
    )
